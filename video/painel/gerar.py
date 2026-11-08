"""Gera um vídeo no estilo "avatar + painel animado" a partir de um roteiro JSON.

Etapas: narração (Google Gemini TTS) -> tempo de cada palavra (Whisper local) ->
linha do tempo (cada animação presa a uma palavra) -> quadros (Chromium) -> mixagem
(voz + ambiente + efeitos do ElevenLabs, já guardados em sons/) -> MP4.

Uso:
    python video/painel/gerar.py roteiro.json saida.mp4 [--rascunho]
"""
from __future__ import annotations

import base64
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import numpy as np
import requests

AQUI = Path(__file__).resolve().parent
CACHE = AQUI / ".cache"
VOZ0 = 0.4  # segundos de respiro antes da primeira palavra


# ---------------------------------------------------------------- texto
def norm(p: str) -> str:
    p = unicodedata.normalize("NFD", p.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", p)


def tokens(texto: str) -> list[str]:
    return [w for w in re.split(r"\s+", texto.strip()) if norm(w)]


# ---------------------------------------------------------------- voz (Gemini)
def narrar(texto: str, voz: dict, destino: Path) -> Path:
    modelo = voz.get("modelo", "gemini-2.5-flash-preview-tts")
    nome = voz.get("nome", "Charon")
    estilo = voz.get("estilo", "Narre em português do Brasil")
    if voz.get("so_texto"):  # modelos que leem a direção em voz alta: só o texto
        prompt = texto
    elif modelo.startswith("gemini-2.5"):
        prompt = f"{estilo}:\n\n{texto}"
    else:  # modelos 3.x: direção em seções (não faladas) + transcrição
        prompt = ("Synthesize speech for the performance below. The PROFILE and PERFORMANCE sections are direction only "
                  "and must never be spoken. Speak only the text under TRANSCRIPT, in Brazilian Portuguese.\n\n"
                  f"### PROFILE\n{voz.get('perfil', 'A mature man with a deep, low voice.')}\n\n"
                  f"### PERFORMANCE\n{voz.get('direcao', estilo)}\n\n### TRANSCRIPT\n{texto}")
    chave = hashlib.sha1(f"{modelo}|{nome}|{prompt}".encode()).hexdigest()[:16]
    wav = CACHE / f"voz_{chave}.wav"
    if wav.exists():
        return wav
    CACHE.mkdir(exist_ok=True)
    modelos = [modelo] + [m for m in ("gemini-2.5-flash-preview-tts", "gemini-3.1-flash-tts-preview") if m != modelo]
    for m in modelos:  # se um modelo estiver sem cota, tenta o próximo
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
            headers={"x-goog-api-key": os.environ.get("GEMINI_API_KEY", "proxy")},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"responseModalities": ["AUDIO"],
                                       "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": nome}}}}},
            timeout=600)
        tentativas = 0
        while r.status_code >= 500 and tentativas < 3:  # erro passageiro: tenta de novo
            tentativas += 1
            r = requests.post(r.url, headers={"x-goog-api-key": "proxy"}, data=r.request.body,
                              timeout=600) if False else requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                headers={"x-goog-api-key": os.environ.get("GEMINI_API_KEY", "proxy")},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"responseModalities": ["AUDIO"],
                                           "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": nome}}}}},
                timeout=600)
        if r.status_code in (429, 404, 403) and m != modelos[-1]:
            print(f"    {m} indisponível ({r.status_code}); tentando o próximo modelo")
            continue
        r.raise_for_status()
        print(f"    voz: {m} ({nome}) — {texto[:40]}…")
        break
    resp = r.json()
    try:
        parte = resp["candidates"][0]["content"]["parts"][0]["inlineData"]
    except (KeyError, IndexError):
        (CACHE / "ultima_resposta.json").write_text(json.dumps(resp, ensure_ascii=False)[:5000])
        motivo = (resp.get("candidates") or [{}])[0].get("finishReason") or resp.get("promptFeedback")
        raise RuntimeError(f"O Gemini não devolveu áudio (motivo: {motivo}).")
    dados = base64.b64decode(parte["data"])
    if "wav" in parte["mimeType"]:
        bruto = CACHE / f"voz_{chave}_orig.wav"
        bruto.write_bytes(dados)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-ar", "48000", "-ac", "1", wav], check=True)
    else:  # PCM 16 bits, 24 kHz
        taxa = int(re.search(r"rate=(\d+)", parte["mimeType"]).group(1))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(taxa), "-ac", "1", "-i", "-",
                        "-ar", "48000", wav], input=dados, check=True)
    return wav


def narrar_blocos(batidas, voz: dict, destino: Path, max_chars=1400) -> Path:
    """Narração longa: agrupa batidas em blocos de até ~max_chars (poucas chamadas, mesma voz/modelo),
    gera em sequência e emenda com a pausa natural entre batidas."""
    blocos, atual = [], []
    for b in batidas:
        if atual and sum(len(x["fala"]) for x in atual) + len(b["fala"]) > max_chars:
            blocos.append(atual); atual = []
        atual.append(b)
    if atual:
        blocos.append(atual)
    print(f"    narração em {len(blocos)} blocos")
    pseudo = [{"fala": "\n".join(x["fala"] for x in bl),
               "pausa_antes": bl[0].get("pausa_antes")} for bl in blocos]
    pseudo = [{k: v for k, v in p.items() if v is not None} for p in pseudo]
    return narrar_batidas(pseudo, voz, destino, paralelo=1)


def narrar_batidas(batidas, voz: dict, destino: Path, paralelo=4) -> Path:
    """Gera a voz frase a frase (chamadas curtas, em paralelo) e emenda com pausas naturais.
    Pausa entre batidas: 0,55 s (0,9 s se a anterior termina em reticências); "pausa_antes" ajusta."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(paralelo) as ex:
        wavs = list(ex.map(lambda b: narrar(b["fala"], voz, CACHE), batidas))
    sr, partes = 48000, []
    for k, (b, w) in enumerate(zip(batidas, wavs)):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", w, "-af",
                              "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.12,areverse,"
                              "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.25,areverse",
                              "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
        a = np.frombuffer(raw, np.float32)
        if k:
            ant = batidas[k - 1]["fala"].rstrip()
            pausa = b.get("pausa_antes", 0.9 if ant.endswith(("...", "…")) else 0.55)
            partes.append(np.zeros(int(pausa * sr), np.float32))
        partes.append(a)
    destino.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", destino],
                   input=np.concatenate(partes).tobytes(), check=True)
    return destino


# ---------------------------------------------------------------- tempo das palavras (Whisper)
def transcrever(wav: Path, roteiro_txt: str):
    from faster_whisper import WhisperModel
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    # sem initial_prompt: com o roteiro como dica o Whisper tende a "pular" a primeira frase
    segs, _ = modelo.transcribe(audio, language="pt", word_timestamps=True)
    return [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in s.words]


def alinhar(palavras_roteiro: list[str], ouvidas):
    """Casa as palavras do roteiro com as ouvidas; as que não casam recebem tempo interpolado."""
    a = [norm(w) for w in palavras_roteiro]
    b = [norm(w) for w, _, _ in ouvidas]
    tempos: list[tuple[float, float] | None] = [None] * len(a)
    for bloco in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(bloco.size):
            _, s, e = ouvidas[bloco.b + k]
            tempos[bloco.a + k] = (s, e)
    conhecidos = [i for i, t in enumerate(tempos) if t]
    if not conhecidos:
        raise RuntimeError("Nenhuma palavra do roteiro foi reconhecida na narração.")
    for i in range(len(tempos)):
        if tempos[i] is None:
            antes = max([k for k in conhecidos if k < i], default=None)
            depois = min([k for k in conhecidos if k > i], default=None)
            if antes is not None and depois is not None:
                f = (i - antes) / (depois - antes)
                s = tempos[antes][1] + (tempos[depois][0] - tempos[antes][1]) * f
            elif antes is not None:
                s = tempos[antes][1] + 0.3 * (i - antes)
            else:
                s = max(0.0, tempos[depois][0] - 0.3 * (depois - i))
            tempos[i] = (s, s + 0.25)
    casadas = len(conhecidos) / len(a)
    return tempos, casadas


def inserir_silencios(wav, tempos, insercoes, destino):
    """Insere silêncio antes da palavra de índice i (no meio da pausa que já existe) e desloca os tempos."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    sr, pedacos, cursor = 48000, [], 0
    tempos = list(tempos)
    desloc = 0.0
    runs = _silencios(a, sr)
    for i, seg in sorted(insercoes):
        t = (tempos[i - 1][1] + tempos[i][0]) / 2 - desloc  # instante no áudio original
        sil = _silencio_entre(runs, tempos[i - 1][1] - desloc - 0.2, tempos[i][0] - desloc + 0.2)
        if sil:
            t = (sil[0] + sil[1]) / 2
        corte = int(t * sr)
        pedacos += [a[cursor:corte], np.zeros(int(seg * sr), np.float32)]
        cursor = corte
        for j in range(i, len(tempos)):
            tempos[j] = (tempos[j][0] + seg, tempos[j][1] + seg)
        desloc += seg
    pedacos.append(a[cursor:])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", destino],
                   input=np.concatenate(pedacos).tobytes(), check=True)
    return destino, tempos


def _silencios(a, sr=48000):
    """Trechos de silêncio REAL (medidos no áudio, quadros de 10 ms), como lista de (inicio, fim) em segundos."""
    q = sr // 100
    n = len(a) // q
    rms = np.sqrt(np.mean(a[: n * q].reshape(n, q) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    fala = np.percentile(db, 90)
    limiar = min(-38.0, max(-58.0, fala - 32.0))
    mudo = db < limiar
    runs, i = [], 0
    while i < n:
        if mudo[i]:
            j = i
            while j < n and mudo[j]:
                j += 1
            if j - i >= 4:  # >= 40 ms
                runs.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    return runs


def _silencio_entre(runs, t0, t1):
    """Maior silêncio real dentro da janela [t0, t1] (recortado à janela), ou None."""
    melhor = None
    for s0, s1 in runs:
        a, b = max(s0, t0), min(s1, t1)
        if b - a > 0 and (melhor is None or b - a > melhor[1] - melhor[0]):
            melhor = (a, b)
    return melhor


def apertar_pausas(wav: Path, palavras, tempos, destino: Path, limites=None):
    """Encurta silêncios longos entre palavras (só encurta, nunca alonga).
    O corte acontece APENAS dentro de silêncio real medido no áudio, com margem de 70 ms de cada lado,
    para nunca comer o fim ou o começo de uma palavra (o Whisper erra as bordas em até ~0,2 s).
    limites = pausa máxima (s) depois de ponto final, reticências, vírgula e entre palavras comuns."""
    L = {"ponto": 0.42, "reticencias": 0.6, "virgula": 0.24, "comum": 0.12}
    L.update(limites or {})
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    sr, pedacos, cursor = 48000, [], 0.0
    runs = _silencios(a, sr)
    margem = 0.07
    cortes = []  # (inicio, fim) de trechos a remover
    for i in range(len(tempos) - 1):
        fim_i, ini_j = tempos[i][1], tempos[i + 1][0]
        w = palavras[i]
        if w.endswith("...") or w.endswith("…"):
            lim = L["reticencias"]
        elif w[-1] in ".!?":
            lim = L["ponto"]
        elif w[-1] in ",;:—":
            lim = L["virgula"]
        else:
            lim = L["comum"]
        sil = _silencio_entre(runs, fim_i - 0.2, ini_j + 0.2)
        if not sil:
            continue
        s0, s1 = sil
        real = s1 - s0
        if real <= lim + 0.08:
            continue
        guarda = max(lim / 2, margem)
        c0, c1 = s0 + guarda, s1 - guarda
        if c1 - c0 >= 0.04:
            cortes.append((c0, c1))
    for c0, c1 in cortes:
        pedacos.append(a[int(cursor * sr):int(c0 * sr)])
        cursor = c1
    pedacos.append(a[int(cursor * sr):])
    f = int(0.012 * sr)  # rampas curtas nas emendas (estão em silêncio, então não se ouvem)
    for k, pd in enumerate(pedacos):
        pd = pd.copy()
        if k > 0 and len(pd) > f:
            pd[:f] *= np.linspace(0, 1, f)
        if k < len(pedacos) - 1 and len(pd) > f:
            pd[-f:] *= np.linspace(1, 0, f)
        pedacos[k] = pd
    out = np.concatenate(pedacos)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", "48000", "-ac", "1", "-i", "-", destino],
                   input=out.astype(np.float32).tobytes(), check=True)

    def mapa(t):
        d = sum(min(c1, max(c0, t)) - c0 for c0, c1 in cortes if t > c0)
        return t - d
    return [(mapa(s0), mapa(e0)) for s0, e0 in tempos]


# ---------------------------------------------------------------- linha do tempo
class Relogio:
    def __init__(self, batidas, tempos, deslocamento):
        self.faixas, i = [], 0
        for b in batidas:
            n = len(tokens(b["fala"]))
            self.faixas.append((i, i + n))
            i += n
        self.palavras = [w for b in batidas for w in tokens(b["fala"])]
        self.t = [(s + deslocamento, e + deslocamento) for s, e in tempos]

    def inicio(self, k):
        return self.t[self.faixas[k][0]][0]

    def fim(self, k):
        return self.t[self.faixas[k][1] - 1][1]

    def indice(self, k, palavra):
        """Índice da palavra (primeira que começa com 'palavra') dentro da batida k."""
        a, b = self.faixas[k]
        if palavra:
            alvo = norm(tokens(palavra)[0])
            for i in range(a, b):
                if norm(self.palavras[i]).startswith(alvo):
                    return i
        return a

    def em(self, k, palavra, padrao=None, fim=False):
        if not palavra:
            return self.inicio(k) if padrao is None else padrao
        alvo = norm(tokens(palavra)[0])
        a, b = self.faixas[k]
        for i in range(a, b):
            if norm(self.palavras[i]).startswith(alvo):
                return self.t[i][1] if fim else self.t[i][0]
        print(f"  aviso: '{palavra}' não está na fala da batida {k + 1}; usei o início dela", file=sys.stderr)
        return self.inicio(k) if padrao is None else padrao


def montar(roteiro, rel: Relogio, duracao, W=1080, H=1920, fps=30):
    tema = json.load(open(AQUI / "temas" / f"{roteiro.get('tema', 'vigia')}.json"))
    nome_av = roteiro.get("avatar", "vigia")
    av_dir = AQUI / "avatares" / nome_av
    av = json.load(open(av_dir / "poses.json"))
    D = {"W": W, "H": H, "fps": fps, "duracao": duracao, "tema": tema,
         "assinatura": roteiro.get("assinatura", ""), "barra": roteiro.get("barra"),
         "avatar": {"base": str(av_dir) + "/", "mediana": av["largura_cabeca_mediana"], "poses": av["poses"]},
         "titulos": [], "poses": [], "paineis": []}
    eventos = []  # efeitos sonoros: (tempo, nome, volume_db)
    atual = None
    base = Path(roteiro["_pasta"])
    for k, b in enumerate(roteiro["batidas"]):
        t0 = rel.inicio(k)
        if b.get("titulo"):
            D["titulos"].append({"t": max(0, t0 - 0.05), "linhas": b["titulo"]})
        for ti in b.get("titulos", []):
            D["titulos"].append({"t": rel.em(k, ti["em"]) - 0.05, "linhas": ti["linhas"]})
        if b.get("pose"):
            D["poses"].append({"t": max(0, t0 - 0.1), "pose": b["pose"]})
        for po in b.get("poses", []):
            D["poses"].append({"t": rel.em(k, po["em"]) - 0.05, "pose": po["pose"]})
        if "painel" not in b:
            continue
        p = b["painel"]
        if p is None:
            if atual:
                atual["t1"] = t0 - 0.1
            atual = None
            continue
        p = json.loads(json.dumps(p))
        continua = p.pop("continua", False) and atual and atual["tipo"] == p.get("tipo", atual["tipo"])
        if not continua:
            if atual:
                atual["t1"] = t0 - 0.15
            p.setdefault("tipo", "lista")
            p["t0"] = max(0.0, t0 - 0.2)
            p["t1"] = duracao
            for chave in ("itens", "campos", "mensagens"):
                p.setdefault(chave, [])
            if p.get("imagem"):
                p["imagem"] = str((base / p["imagem"]).resolve())
            D["paineis"].append(p)
            eventos.append((p["t0"], "whoosh", -16))
            alvo = p
        else:
            alvo = atual
            for chave in ("itens", "campos", "mensagens"):
                alvo.setdefault(chave, []).extend(p.get(chave, []))
            for ch, v in p.items():
                if ch not in ("itens", "campos", "mensagens", "tipo"):
                    alvo[ch] = v
        # resolve âncoras dos elementos desta batida
        for it in p.get("itens", []):
            it["t"] = rel.em(k, it.get("em"))
            if it.get("riscar"):
                it["risco_t"] = rel.em(k, it["riscar"], fim=True)
            if it.get("marcar"):
                it["marca_t"] = rel.em(k, it["marcar"], fim=True)
            eventos.append((it["t"], "tecla", -20))
        for c in p.get("campos", []):
            c["t"] = rel.em(k, c.get("em"))
            eventos.append((c["t"], "tecla", -20))
        for m in p.get("mensagens", []):
            m["t"] = rel.em(k, m.get("em"))
        if p.get("carimbo"):
            alvo["carimbo"]["t"] = rel.em(k, p["carimbo"].get("em"), fim=True)
            eventos.append((alvo["carimbo"]["t"], "impacto", -8))
        if p.get("tipo") == "impacto" or (continua and alvo["tipo"] == "impacto" and p.get("grande")):
            alvo["t_grande"] = rel.em(k, p.get("em_grande"), padrao=alvo["t0"] + 0.8)
            eventos.append((alvo["t_grande"], "impacto", -6))
        if p.get("tipo") == "contador":
            alvo["t_contagem"] = rel.em(k, p.get("em_contagem"), padrao=alvo["t0"] + 0.3)
            if p.get("em_nota"):
                alvo["t_nota"] = rel.em(k, p["em_nota"])
        if p.get("tipo") == "imagem" and p.get("em_legenda"):
            alvo["t_legenda"] = rel.em(k, p["em_legenda"])
        atual = alvo
    D["titulos"].sort(key=lambda x: x["t"])
    D["poses"].sort(key=lambda x: x["t"])
    return D, eventos


# ---------------------------------------------------------------- áudio
def mixar(voz_wav, inicio_voz, duracao, eventos, trilha, saida):
    sons = AQUI / "sons"
    ent = ["-i", str(voz_wav)]
    filtros = [f"[0:a]aresample=48000,highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=5:release=150,"
               f"adelay={int(inicio_voz * 1000)}:all=1,apad,atrim=0:{duracao:.3f},asplit=2[voz][chave]"]
    rot = ["[voz]"]
    n = 1
    if trilha and trilha.get("ambiente"):
        ent += ["-stream_loop", "-1", "-i", str(sons / f"{trilha['ambiente']}.mp3")]
        filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=mono,volume={trilha.get('volume_db', -20)}dB,"
                       f"atrim=0:{duracao:.3f},afade=t=in:d=1.2,afade=t=out:st={max(0, duracao - 2):.3f}:d=2[amb0]")
        filtros.append("[amb0][chave]sidechaincompress=threshold=0.04:ratio=4:attack=40:release=500[amb]")
        rot.append("[amb]")
        n += 1
    else:
        filtros.append("[chave]anullsink")
    for t, nome, vol in eventos:
        arq = sons / f"{nome}.mp3"
        if not arq.exists() or t >= duracao:
            continue
        ent += ["-i", str(arq)]
        ms = max(0, int(t * 1000))
        filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=mono,volume={vol}dB,adelay={ms}:all=1[e{n}]")
        rot.append(f"[e{n}]")
        n += 1
    filtros.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=first,atrim=0:{duracao:.3f}[mix]")
    bruto = str(saida) + ".bruto.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", ";".join(filtros), "-map", "[mix]",
                    bruto], check=True)
    med = subprocess.run(["ffmpeg", "-i", bruto, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-af",
                    f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
                    "linear=true,aresample=48000,alimiter=limit=0.79:attack=1:release=50:level=disabled", "-ac", "2", saida], check=True)
    os.remove(bruto)


# ================================================================ modo CENAS (imagens em tela cheia)
def quebrar_linhas(palavras, max_chars):
    """Divide em até 2 linhas equilibradas."""
    txt = " ".join(palavras)
    if len(txt) <= max_chars:
        return [txt]
    melhor, m = None, 1e9
    for i in range(1, len(palavras)):
        a, b = " ".join(palavras[:i]), " ".join(palavras[i:])
        custo = abs(len(a) - len(b)) + (1000 if max(len(a), len(b)) > max_chars else 0)
        if custo < m:
            melhor, m = [a, b], custo
    return melhor


def blocos_legenda(rel: Relogio, max_chars=26):
    """Frases curtas (até 2 linhas): quebra em fim de frase; frases longas quebram em vírgula/reticências."""
    blocos, atual = [], []
    lim = 2 * max_chars
    for i, w in enumerate(rel.palavras):
        atual.append(i)
        txt = " ".join(rel.palavras[j] for j in atual)
        prox = rel.palavras[i + 1] if i + 1 < len(rel.palavras) else None
        fim_frase = w[-1] in ".!?" or w.endswith("…")
        pausa = w[-1] in ",;:" or w.endswith("...")
        cabe_prox = prox is not None and len(txt) + 1 + len(prox) <= lim
        if fim_frase or prox is None or not cabe_prox or (pausa and len(txt) > max_chars * 0.9):
            blocos.append(atual)
            atual = []
    saida = []
    for k, b in enumerate(blocos):
        t0 = rel.t[b[0]][0] - 0.05
        prox_t0 = rel.t[blocos[k + 1][0]][0] - 0.05 if k + 1 < len(blocos) else None
        t1 = rel.t[b[-1]][1] + 0.7
        if prox_t0 is not None:
            t1 = min(t1, prox_t0 - 0.02)
        saida.append({"t0": t0, "t1": t1, "linhas": quebrar_linhas([rel.palavras[j] for j in b], max_chars)})
    return saida


def envelope_voz(wav, inicio, duracao, fps=30):
    """Intensidade da voz por quadro (0..1), suavizada: anima o Vigia como se estivesse falando."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    n, passo = int(duracao * fps) + 1, 48000 // fps
    env = np.zeros(n)
    for k in range(n):
        i = int((k / fps - inicio) * 48000)
        if 0 <= i < len(a):
            env[k] = np.sqrt(np.mean(a[i:i + passo] ** 2) + 1e-12)
    env = env / (np.percentile(env[env > 0], 95) if (env > 0).any() else 1)
    out, v = [], 0.0
    for x in np.clip(env, 0, 1):  # ataque rápido, soltura lenta
        v = v + (x - v) * (0.55 if x > v else 0.12)
        out.append(round(float(v), 3))
    return out


# palavras que pedem uma pose de conversa específica (se existir no avatar); o resto é sorteado
DICAS_CONVERSA = [
    (r"\?", ["c_dar_de_ombros", "c_mao_aberta_lado"]),
    (r"\b(nao|nunca|nenhum|nenhuma|ninguem|nada|vazio|vazia)\b", ["c_serio_frontal", "c_desconfiado_lado", "c_preocupado"]),
    (r"\b(madrugada|noite|chovia|chuva|estrada|ceu)\b", ["c_olhar_cima", "c_falando_olhar_lado"]),
    (r"\b(certeza|sozinho|sabia|achava)\b", ["c_mao_no_peito", "c_falando_inclinado"]),
    (r"\b(duas|tres|uma|primeira|segunda|cada)\b", ["c_dedo_explicando"]),
    (r"\b(olhou|olhar|olhando|viu|ver)\b", ["c_falando_olhar_lado", "c_desconfiado_lado"]),
    (r"\b(seguinte|depois|entao|quando)\b", ["c_falando", "c_oferecendo"]),
]


def fronteira(rel: "Relogio", i: int) -> float:
    """Instante para trocar de pose ANTES da palavra i: no silêncio entre a palavra anterior e ela
    (pouco antes dela começar); se não houver silêncio, exatamente na junção das duas."""
    ini = rel.t[i][0]
    if i == 0:
        return max(0.0, ini - 0.1)
    fim_ant = rel.t[i - 1][1]
    if ini <= fim_ant:
        return ini
    return max(fim_ant + 0.02, ini - 0.1)


def poses_de_conversa(fixas, rel: Relogio, poses, roteiro, duracao, semente=7):
    """Poses de CONVERSA trocadas só nas pausas da narração: fim de frase (sempre), vírgula/reticências
    com pausa real, ou pausa longa no meio da frase. A troca cai no silêncio antes da nova frase, e a
    pose é escolhida pelo conteúdo do trecho quando possível. ÊNFASES seguram e depois a conversa volta."""
    import random
    rnd = random.Random(semente)
    pools = {}
    for k, v in poses.items():
        pools.setdefault(v.get("grupo", "conversa"), []).append(k)
    pesos = {k: v.get("peso", 3) for k, v in poses.items()}
    batida_de = {ii: kb for kb, (a0, a1) in enumerate(rel.faixas) for ii in range(a0, a1)}
    ocupado = []
    for i, p in enumerate(fixas):
        fim = p["t"] + p.get("segurar", 1.6)
        if i + 1 < len(fixas):
            fim = min(fim, fixas[i + 1]["t"])
        ocupado.append((p["t"], fim))
    livre = lambda t: all(not (a - 0.3 <= t < b) for a, b in ocupado)
    # começo de frase nova pode encerrar uma ênfase que já cumpriu boa parte do tempo
    livre_frase = lambda t: all(not (a - 0.1 <= t < a + 0.6) for a, b in ocupado)
    W = rel.palavras
    novas, ultimo, recentes = [], -9.0, []
    for i in range(len(W)):
        t = fronteira(rel, i)
        ant = W[i - 1] if i else ""
        pausa = rel.t[i][0] - rel.t[i - 1][1] if i else 9
        fim_frase = i == 0 or ant.endswith(("...", "…")) or ant[-1:] in ".!?"
        virgula = ant[-1:] in ",;:—"
        desde = t - ultimo
        if fim_frase:
            ok = desde >= 1.0
        elif virgula:
            ok = pausa >= 0.12 and desde >= 1.8
        else:
            ok = pausa >= 0.35 and desde >= 3.0
        disponivel = livre_frase(t) if fim_frase else livre(t)
        # conta o tempo desde a última troca, inclusive ênfases já passadas
        for a0, _ in ocupado:
            if a0 <= t:
                ultimo = max(ultimo, a0)
        desde = t - ultimo
        if fim_frase:
            ok = desde >= 1.0
        elif virgula:
            ok = pausa >= 0.12 and desde >= 1.8
        else:
            ok = pausa >= 0.35 and desde >= 3.0
        # não troca se uma ênfase vai entrar logo em seguida (evita duas trocas seguidas)
        if any(t < a0 <= t + 1.1 for a0, _ in ocupado):
            continue
        if not ok or not disponivel:
            continue
        # trecho que será dito com esta pose (até a próxima pausa de frase)
        j = i
        while j < len(W) - 1 and W[j][-1:] not in ".!?,;:" and not W[j].endswith("..."):
            j += 1
        trecho = norm_frase(" ".join(W[i:j + 1]))
        tom = roteiro["batidas"][batida_de.get(i, 0)].get("tom", "conversa")
        pool = pools.get(tom) or pools["conversa"]
        escolha = None
        if tom == "conversa":
            for padrao, opcoes in DICAS_CONVERSA:
                if re.search(padrao, trecho):
                    opc = [o for o in opcoes if o in pool and o not in recentes[-2:]]
                    if opc:
                        escolha = rnd.choice(opc)
                        break
        if not escolha:
            cand = [k for k in pool if k not in recentes[-3:]] or pool
            escolha = rnd.choices(cand, weights=[pesos[k] for k in cand])[0]
        novas.append({"t": t, "pose": escolha, "tipo": "conversa"})
        recentes.append(escolha)
        ultimo = t
    return sorted(fixas + novas, key=lambda p: p["t"])


def norm_frase(txt):
    txt = unicodedata.normalize("NFD", txt.lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9?\s]", " ", txt)


def montar_cenas(roteiro, rel: Relogio, duracao, W=1080, H=1920, fps=30):
    tema = json.load(open(AQUI / "temas" / f"{roteiro.get('tema', 'vigia')}.json"))
    av_dir = AQUI / "avatares" / roteiro.get("avatar", "vigia")
    av = json.load(open(av_dir / "poses.json"))
    base = Path(roteiro["_pasta"])
    leg = roteiro.get("legendas", {})
    D = {"modo": "cenas", "W": W, "H": H, "fps": fps, "duracao": duracao, "tema": tema,
         "avatar": {"base": str(av_dir) + "/", "tipo": av.get("tipo", "busto"),
                    "mediana": av.get("largura_cabeca_mediana"), "poses": av["poses"]},
         "canto": roteiro.get("canto", {"x": 30, "w": 285, "base": H - 340} if H > W else {"x": 40, "w": 250, "base": H - 10}),
         # Vigia em destaque (no cenário dele): maior, no terço esquerdo
         "canto_destaque": roteiro.get("canto_destaque", {"x": 60, "w": 560, "base": H + 40} if W > H else {"x": 140, "w": 520, "base": H - 300}),
         "legenda_y": leg.get("y", 1190 if H > W else H - 92), "legenda_tam": leg.get("tamanho", 56 if H > W else 50),
         "chuva": roteiro.get("chuva", 0), "grao": roteiro.get("grao", 0.16),
         "cenas": [], "poses": [], "legendas": [], "escuros": []}
    plano = {"ambientes": [], "musica": roteiro.get("musica"), "trilhas": [], "efeitos": [], "abafar": [], "quedas": [],
             "fim_musica": rel.t[-1][1]}
    for amb in roteiro.get("ambiente_inicial", []):
        plano["ambientes"].append({"t": 0.0, **amb})
    ab = roteiro.get("abertura")
    if ab and not (base / ab["imagem"]).exists() and (base / "provisorias" / Path(ab["imagem"]).name).exists():
        ab = dict(ab, imagem="provisorias/" + Path(ab["imagem"]).name)
    if ab and ab.get("antes_da_batida"):
        kb = ab["antes_da_batida"]
        t_a0, t_a1 = rel.fim(kb - 1) + 0.3, rel.inicio(kb) - 0.3
        D["_abertura_meio"] = {"t0": t_a0, "imagem": str((base / ab["imagem"]).resolve()), "zoom": ab.get("zoom", [1.06, 1.0]),
                               "foco": ab.get("foco", [[0.5, 0.4], [0.5, 0.4]]), "relampagos": ab.get("relampagos", [0.12, 0.42]),
                               "abertura": True}
        D["abertura_janela"] = [t_a0, t_a1]
        for so in ab.get("sons", [{"som": "impacto", "t": 0.1, "volume_db": -6, "grave": True}]):
            plano["efeitos"].append({"t": t_a0 + so["t"], "som": so["som"], "volume_db": so.get("volume_db", -8),
                                     "grave": so.get("grave", False)})
        ab = None
    if ab:  # cartão de abertura: relâmpago + trovão, aproximação lenta, corte seco para a 1ª cena
        D["cenas"].append({"t0": 0.0, "imagem": str((base / ab["imagem"]).resolve()), "zoom": ab.get("zoom", [1.06, 1.0]),
                           "foco": ab.get("foco", [[0.5, 0.4], [0.5, 0.4]]), "relampagos": ab.get("relampagos", [0.12, 0.42]),
                           "abertura": True})
        D["abertura_fim"] = ab["duracao"]
        for so in ab.get("sons", [{"som": "impacto", "t": 0.1, "volume_db": -6, "grave": True}]):
            plano["efeitos"].append({"t": so["t"], "som": so["som"], "volume_db": so.get("volume_db", -8),
                                     "grave": so.get("grave", False)})
    for k, b in enumerate(roteiro["batidas"]):
        t0 = rel.inicio(k)
        cenas = ([b["cena"]] if b.get("cena") else []) + b.get("cenas", [])
        for c in cenas:
            c = dict(c)
            if not D["cenas"]:
                c["t0"] = 0.0
            elif D["cenas"][-1].get("abertura") and len(D["cenas"]) == 1:
                c.pop("em", None); c["t0"] = D["abertura_fim"]
            else:
                c["t0"] = fronteira(rel, rel.indice(k, c.pop("em", None)))
            if not c.get("imagem"):  # cena desenhada no motor (ex.: relógio)
                D["cenas"].append(c)
                continue
            arq = base / c["imagem"]
            if not arq.exists():  # imagem ainda não entregue: usa a provisória com o mesmo nome, se houver
                prov = base / "provisorias" / arq.name
                if prov.exists():
                    print(f"  aviso: {c['imagem']} não existe; usando provisória {prov.name}", file=sys.stderr)
                    arq = prov
            c["imagem"] = str(arq.resolve())
            D["cenas"].append(c)
        if b.get("pose"):
            D["poses"].append({"t": max(0.0, t0 - 0.08) if D["poses"] else 0.0, "pose": b["pose"]})
        for po in b.get("poses", []):
            D["poses"].append({"t": rel.em(k, po["em"]) - 0.06, "pose": po["pose"]})
        for so in b.get("sons", []):
            plano["efeitos"].append({"t": rel.em(k, so.get("em"), fim=so.get("depois", False)) + so.get("atraso", 0),
                                     "som": so["som"], "volume_db": so.get("volume_db", -10), "grave": so.get("grave", False)})
        if b.get("musica"):
            if not plano["trilhas"] and roteiro.get("musica"):
                plano["trilhas"].append({"t": 0.0, **roteiro["musica"]})
            mu = b["musica"]
            plano["trilhas"].append({"t": rel.em(k, mu.get("em")), "som": mu["som"], "volume_db": mu.get("volume_db", -12)})
        if b.get("ambiente"):
            a = b["ambiente"]
            plano["ambientes"].append({"t": rel.em(k, a.get("em")), "som": a["som"], "volume_db": a.get("volume_db", -6)})
        for chave in ("abafar", "queda"):
            if b.get(chave):
                x = b[chave]
                ini = rel.em(k, x.get("de"))
                fim = rel.em(k, x["ate"], fim=True) if x.get("ate") else rel.fim(k)
                fim += x.get("mais", 0)
                (plano["abafar"] if chave == "abafar" else plano["quedas"]).append((ini, fim, x.get("forca", 0.5)))
                if chave == "queda" and x.get("escurecer"):
                    D["escuros"].append({"t0": ini, "t1": fim, "forca": x["escurecer"]})
    if D.get("_abertura_meio"):
        D["cenas"].append(D.pop("_abertura_meio"))
    D["cenas"].sort(key=lambda c: c["t0"])
    for i, c in enumerate(D["cenas"]):
        c["t1"] = D["cenas"][i + 1]["t0"] if i + 1 < len(D["cenas"]) else duracao
    # lado do Vigia: muda só num corte de imagem, para o lado oposto ao assunto da cena,
    # e no máximo a cada ~15 s (ou quando o roteiro pede "lado": "esq"/"dir")
    lado, ultima = roteiro.get("lado_inicial", "esq"), -99.0
    for c in D["cenas"]:
        if c.get("lado"):
            if c["lado"] != lado:
                lado, ultima = c["lado"], c["t0"]
        elif not (c.get("vigia") or c.get("abertura") or c.get("tipo") == "relogio") and c.get("foco"):
            fx = c["foco"][1][0]
            quer = "dir" if fx < 0.42 else "esq" if fx > 0.58 else None
            if quer and quer != lado and c["t0"] - ultima >= roteiro.get("lado_intervalo", 15):
                lado, ultima = quer, c["t0"]
        c["lado"] = lado
    for k, b in enumerate(roteiro["batidas"]):
        for en in b.get("enfase", []):
            D["poses"].append({"t": fronteira(rel, rel.indice(k, en["em"])), "pose": en["pose"], "tipo": "enfase",
                               "segurar": en.get("segurar", 1.8)})
    cta = roteiro.get("cta")
    if cta:  # tela final de chamada para o YouTube
        t_cta = rel.t[-1][1] + roteiro.get("cauda", 1.6)
        D["cta"] = {"t0": t_cta, "titulo": cta.get("titulo"), "canal": cta.get("canal"), "subtitulo": cta.get("subtitulo")}
        if cta.get("fundo"):  # chamada final no cenário do Vigia, com ele em destaque
            D["cenas"].append({"t0": t_cta, "t1": duracao, "imagem": str((base / cta["fundo"]).resolve()),
                               "zoom": [1.0, 1.04], "foco": [[0.5, 0.5], [0.5, 0.5]], "vigia": True, "lado": "esq",
                               "encaixe": "cobrir"})
            D["cenas"].sort(key=lambda c: c["t0"])
            for i, c in enumerate(D["cenas"][:-1]):
                c["t1"] = D["cenas"][i + 1]["t0"]
        plano["efeitos"] += [{"t": t_cta, "som": "whoosh", "volume_db": -10},
                             {"t": t_cta + 1.35, "som": "tecla", "volume_db": -2}]
        if cta.get("pose"):
            D["poses"].append({"t": t_cta + 0.2, "pose": cta["pose"], "tipo": "enfase", "segurar": 9})
    D["poses"].sort(key=lambda p: p["t"])
    if any(p.get("grupo") == "conversa" for p in av["poses"].values()):
        D["poses"] = poses_de_conversa(D["poses"], rel, av["poses"], roteiro, duracao)
    dest = [norm(w) for w in leg.get("destaques", [])]
    for bl in blocos_legenda(rel, leg.get("max_caracteres", 26 if H > W else 42)):
        bl["destaques"] = dest
        D["legendas"].append(bl)
    return D, plano


def mixar_cenas(voz_wav, inicio_voz, duracao, plano, saida):
    sons = AQUI / "sons"
    ent = ["-i", str(voz_wav)]
    f = [f"[0:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=2.2:attack=8:release=180,"
         f"adelay={int(inicio_voz * 1000)}:all=1,apad,atrim=0:{duracao:.3f},asplit=2[voz][chave]"]
    n, camas = 1, []
    amb = sorted(plano["ambientes"], key=lambda a: a["t"])
    for i, a in enumerate(amb):  # ambientes em sequência, com fusão de 0,8 s
        ini = max(0.0, a["t"] - 0.4)
        fim = amb[i + 1]["t"] + 0.4 if i + 1 < len(amb) else duracao
        if a["som"] in (None, "nenhum", "silencio"):  # trecho sem ambiente
            continue
        ent += ["-stream_loop", "-1", "-i", str(sons / f"{a['som']}.mp3")]
        fi = 0.8 if i else 0.6
        f.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{fim - ini:.3f},asetpts=PTS-STARTPTS,"
                 f"volume={a.get('volume_db', -6)}dB,afade=t=in:d={fi},afade=t=out:st={max(0, fim - ini - 0.8):.3f}:d=0.8,"
                 f"adelay={int(ini * 1000)}:all=1[amb{n}]")
        camas.append(f"[amb{n}]")
        n += 1
    # trilhas musicais em sequência (troca com fusão de 2 s); a última some no fim da narração
    trilhas = sorted(plano.get("trilhas") or ([{"t": 0.0, **plano["musica"]}] if plano.get("musica") else []),
                     key=lambda x: x["t"])
    fim_m = plano["fim_musica"] + 0.3
    for i, m in enumerate(trilhas):
        ini = max(0.0, m["t"] - 1.0)
        fim = min(fim_m, trilhas[i + 1]["t"] + 1.0) if i + 1 < len(trilhas) else fim_m
        if fim <= ini or m["som"] in (None, "nenhum", "silencio"):  # silêncio: nenhuma trilha nesse trecho
            continue
        ent += ["-stream_loop", "-1", "-i", str(sons / f"{m['som']}.mp3")]
        fi = 2.5 if i == 0 else 2.0
        fo = 2.0
        f.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{fim - ini:.3f},asetpts=PTS-STARTPTS,"
                 f"volume={m.get('volume_db', -12)}dB,afade=t=in:d={fi},afade=t=out:st={max(0, fim - ini - fo):.3f}:d={fo},"
                 f"adelay={int(ini * 1000)}:all=1[mus{n}]")
        camas.append(f"[mus{n}]")
        n += 1
    if not camas:
        f.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{duracao:.3f}[vazio]")
        camas.append("[vazio]")
    cama = "[cama0]"
    f.append(f"{''.join(camas)}amix=inputs={len(camas)}:normalize=0:duration=longest,apad,atrim=0:{duracao:.3f}{cama}")
    # automações: som abafado (passa-baixa) e quedas de volume
    cadeia = []
    for a0, a1, _ in plano["abafar"]:
        cadeia.append(f"lowpass=f=650:enable='between(t,{a0:.2f},{a1:.2f})'")
    for q0, q1, forca in plano["quedas"]:
        cadeia.append(f"volume={1 - forca:.2f}:enable='between(t,{q0:.2f},{q1:.2f})'")
    f.append(f"{cama}{','.join(cadeia) if cadeia else 'anull'}[cama1]")
    f.append("[cama1][chave]sidechaincompress=threshold=0.05:ratio=2.5:attack=60:release=700[camad]")
    rot = ["[voz]", "[camad]"]
    for e in plano["efeitos"]:
        arq = sons / f"{e['som']}.mp3"
        if not arq.exists() or e["t"] >= duracao:
            print(f"  aviso: efeito '{e['som']}' ignorado", file=sys.stderr)
            continue
        ent += ["-i", str(arq)]
        extra = "lowpass=f=220,bass=g=4," if e.get("grave") else ""
        f.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,{extra}volume={e['volume_db']}dB,"
                 f"adelay={max(0, int(e['t'] * 1000))}:all=1[e{n}]")
        rot.append(f"[e{n}]")
        n += 1
    f.append(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=first,atrim=0:{duracao:.3f}[mix]")
    bruto = str(saida) + ".bruto.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", ";".join(f), "-map", "[mix]", bruto], check=True)
    med = subprocess.run(["ffmpeg", "-i", bruto, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    mm = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-af",
                    f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
                    f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}:"
                    "linear=true,aresample=48000,alimiter=limit=0.79:attack=1:release=50:level=disabled", "-ac", "2", saida], check=True)
    os.remove(bruto)


# ---------------------------------------------------------------- principal
def gerar(caminho_roteiro, saida, rascunho=False):
    roteiro = json.load(open(caminho_roteiro, encoding="utf-8"))
    roteiro["_pasta"] = str(Path(caminho_roteiro).resolve().parent)
    batidas = roteiro["batidas"]
    texto = "\n".join(b["fala"] for b in batidas)
    print("1/5 narração (Gemini)…")
    if roteiro.get("voz_arquivo"):  # narração já existente (ex.: trecho do episódio longo para um Short)
        wav = (Path(roteiro["_pasta"]) / roteiro["voz_arquivo"]).resolve()
        print(f"    usando narração existente: {wav.name}")
    elif len(texto) > roteiro.get("voz_max_chars", 1600):
        wav = narrar_blocos(batidas, roteiro.get("voz", {}), CACHE / f"blocos_{os.getpid()}.wav",
                            roteiro.get("voz_max_chars", 1400))
    elif roteiro.get("voz_por_frase", False):
        wav = narrar_batidas(batidas, roteiro.get("voz", {}), CACHE / f"emendada_{os.getpid()}.wav")
    else:
        wav = narrar(texto, roteiro.get("voz", {}), CACHE)
    print("2/5 tempo das palavras (Whisper)…")
    palavras = [w for b in batidas for w in tokens(b["fala"])]
    ouvidas = transcrever(wav, texto)
    tempos, casadas = alinhar(palavras, ouvidas)
    print(f"    {casadas:.0%} das palavras reconhecidas")
    if casadas < 0.7:
        print("    aviso: narração muito diferente do roteiro (a voz pode ter lido instruções ou pulado trechos)")
    # corta o que vier antes da primeira palavra do roteiro (ex.: instrução de estilo lida em voz alta)
    corte = max(0.0, tempos[0][0] - 0.3)  # folga: o Whisper pode marcar o início da 1ª palavra tarde
    tmp = Path(tempfile.mkdtemp(prefix="painel_"))
    voz_cortada = tmp / "voz_inicio.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{corte:.3f}", "-i", wav, voz_cortada], check=True)
    tempos = [(s - corte, e - corte) for s, e in tempos]
    if roteiro.get("apertar_pausas", True):
        antes = tempos[-1][1]
        voz_final = tmp / "voz.wav"
        tempos = apertar_pausas(voz_cortada, palavras, tempos, voz_final, roteiro.get("pausas"))
        voz_cortada = voz_final
        print(f"    pausas encurtadas: {antes:.1f} s -> {tempos[-1][1]:.1f} s")
    # silêncios dramáticos pedidos no roteiro ("pausa_antes_s" na batida) — inseridos depois do aperto
    insercoes, i0 = [], 0
    for b in batidas:
        n_pal = len(tokens(b["fala"]))
        if b.get("pausa_antes_s") and i0 > 0:
            insercoes.append((i0, float(b["pausa_antes_s"])))
        i0 += n_pal
    if insercoes:
        voz_cortada, tempos = inserir_silencios(voz_cortada, tempos, insercoes, tmp / "voz_pausas.wav")
    ab = roteiro.get("abertura")
    meio = bool(ab and ab.get("antes_da_batida"))
    inicio_voz = (ab["duracao"] + ab.get("respiro", 0.15)) if (ab and not meio) else VOZ0
    roteiro["_inicio_voz"] = inicio_voz
    rel = Relogio(batidas, tempos, inicio_voz)
    fim_voz = rel.t[-1][1]
    duracao = round(fim_voz + roteiro.get("cauda", 1.6) + (roteiro["cta"].get("duracao", 3.6) if roteiro.get("cta") else 0), 2)
    print(f"    narração: {fim_voz - VOZ0:.1f} s")
    if roteiro.get("modo") == "cenas":
        W, H = {"9:16": (1080, 1920), "16:9": (1920, 1080)}[roteiro.get("formato", "9:16")]
        D, plano = montar_cenas(roteiro, rel, duracao, W, H)
        D["voz_env"] = envelope_voz(voz_cortada, roteiro["_inicio_voz"], duracao)
    else:
        D, eventos = montar(roteiro, rel, duracao)
    (tmp / "linha.json").write_text(json.dumps(D, ensure_ascii=False))
    print(f"3/5 quadros ({duracao:.1f} s)…")
    cmd = ["node", str(AQUI / "render.js"), str(tmp / "linha.json"), str(tmp / "video.mp4")]
    if rascunho:
        cmd.append("--rascunho")
    subprocess.run(cmd, check=True)
    print("4/5 mixagem…")
    if roteiro.get("modo") == "cenas":
        mixar_cenas(voz_cortada, roteiro["_inicio_voz"], duracao, plano, str(tmp / "audio.wav"))
    else:
        mixar(voz_cortada, VOZ0, duracao, eventos, roteiro.get("trilha"), str(tmp / "audio.wav"))
    print("5/5 finalizando…")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp / "video.mp4", "-i", tmp / "audio.wav", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "19", "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", saida], check=True)
    json.dump({"palavras": [(w, round(s, 2), round(e, 2)) for w, (s, e) in zip(palavras, rel.t)],
               "poses": [(round(p["t"], 2), p["pose"], p.get("tipo")) for p in D.get("poses", [])]},
              open(str(saida) + ".tempos.json", "w"), ensure_ascii=False)
    print(f"pronto: {saida}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    gerar(a[0], a[1], rascunho="--rascunho" in sys.argv)
