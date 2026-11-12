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
import shutil
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


def ajustar_inicios(wav, tempos, janela=(0.8, 1.2)):
    """10/11: o Whisper marca o início de frases depois de pausa CEDO demais (até 1 s no diálogo do Aurélio,
    Ep. 04) — e os cortes/legendas seguem esse tempo, deixando o som "atrasado da imagem". Aqui cada palavra
    que vem depois de uma pausa tem o início encostado no fim do silêncio REAL mais próximo (medido no áudio)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    runs = [r for r in _silencios(np.frombuffer(raw, np.float32)) if r[1] - r[0] >= 0.12]
    novos, mudou = list(tempos), 0
    for i in range(1, len(novos)):
        s0, e0 = novos[i]
        perto = [r for r in runs if s0 - janela[0] <= r[1] <= s0 + janela[1] and r[1] > novos[i - 1][0] + 0.05]
        if not perto:
            continue
        r = min(perto, key=lambda r: abs(r[1] - s0))
        ini = r[1] + 0.02
        if abs(ini - s0) < 0.08 or ini >= e0 + 0.6 or (i + 1 < len(novos) and ini >= novos[i + 1][0] - 0.05):
            continue
        novos[i] = (ini, max(e0, ini + 0.08))
        if novos[i - 1][1] > r[0]:  # a palavra anterior termina onde o silêncio começa
            novos[i - 1] = (novos[i - 1][0], max(novos[i - 1][0] + 0.05, r[0]))
        mudou += 1
    print(f"    inícios de frase ajustados ao áudio real: {mudou}")
    return novos


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
        t_ant, t_prox = tempos[i - 1][1] - desloc, tempos[i][0] - desloc
        t = (t_ant + t_prox) / 2  # instante no áudio original
        # 10/11: a pausa vai no silêncio real que fica IMEDIATAMENTE antes da próxima palavra (o mais próximo
        # do início dela), e nunca antes do fim da palavra anterior. O Whisper erra os limites às vezes: no
        # Ep. 04 o fim de "olhar." veio cedo e a pausa cortou a palavra ao meio ("glitch").
        cand = [(s0, s1) for s0, s1 in runs if s1 - s0 >= 0.06 and s1 > t_ant - 0.1 and s0 < t_prox + 0.6]
        if cand:
            s0, s1 = min(cand, key=lambda r: abs(min(r[1], t_prox + 0.6) - t_prox))
            t = (max(s0, t_ant - 0.1) + min(s1, t_prox + 0.6)) / 2
        else:  # sem silêncio: o trecho de 30 ms mais quieto entre as duas palavras
            j0, j1 = int((t_ant - 0.1) * sr), int((t_prox + 0.3) * sr)
            q = int(0.03 * sr)
            seg_ = a[max(0, j0):j1]
            if len(seg_) > q:
                e_ = np.convolve(seg_ ** 2, np.ones(q) / q, mode="valid")
                t = (max(0, j0) + int(np.argmin(e_)) + q // 2) / sr
            print(f"    aviso: pausa sem silêncio real por perto (palavra {i}); corte no ponto mais quieto")
        corte = int(t * sr)
        # 13/11: fade curto nos dois lados do corte (antes o corte era seco e às vezes "comia" o fim da palavra)
        pedaco = a[cursor:corte].copy(); nf = min(len(pedaco), int(0.015 * sr))
        if nf: pedaco[-nf:] *= np.linspace(1, 0, nf, dtype=np.float32)
        if cursor and pedacos:
            ni = min(len(pedaco), int(0.015 * sr)); pedaco[:ni] *= np.linspace(0, 1, ni, dtype=np.float32)
        pedacos += [pedaco, np.zeros(int(seg * sr), np.float32)]
        cursor = corte
        for j in range(i, len(tempos)):
            tempos[j] = (tempos[j][0] + seg, tempos[j][1] + seg)
        desloc += seg
    resto = a[cursor:].copy(); ni = min(len(resto), int(0.015 * sr))
    if cursor and ni: resto[:ni] *= np.linspace(0, 1, ni, dtype=np.float32)
    pedacos.append(resto)
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
    # 10/11: o limiar acompanha o ruído de fundo da própria narração (6 dB acima dele); antes ficava abaixo do
    # "chão" de ruído do Gemini (~-49 dB) e quase nenhuma pausa real era reconhecida
    limiar = min(-38.0, max(-58.0, fala - 32.0, float(np.percentile(db, 10)) + 6.0))
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
                    "linear=true,aresample=48000,alimiter=limit=0.70:attack=1:release=50:level=disabled", "-ac", "2", saida], check=True)
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


def trilha_digitacao(c, dur_max):
    """Gera (e guarda em cache) o áudio de digitação de uma tela de texto: teclado mecânico (clicky),
    um clique gravado por letra (sorteado entre 13), ritmo humano irregular e barra de espaço mais grave."""
    import random
    txt = c.get("texto", "").replace("\n", "")
    cps = c.get("cps", 22)
    chave = hashlib.sha1(f"mec1|{txt}|{cps}|{dur_max:.2f}".encode()).hexdigest()[:14]
    arq = CACHE / f"digitacao_{chave}.wav"
    if arq.exists():
        return arq
    cliques = np.load(AQUI / "sons" / "teclado_mecanico_clicks.npy").astype(np.float32)
    cliques = cliques / (np.abs(cliques).max(axis=1, keepdims=True) + 1e-9)
    sr, rnd = 48000, random.Random(chave)
    out = np.zeros(int((dur_max + 0.3) * sr), np.float32)
    ultimo = -1
    for k, ch in enumerate(txt):
        t = 0.25 + k / cps
        if t > dur_max:
            break
        i = rnd.randrange(len(cliques))
        if i == ultimo:
            i = (i + 1) % len(cliques)
        ultimo = i
        x = cliques[i] * rnd.uniform(0.6, 1.0)
        if ch == " ":  # barra de espaço: mais cheia e um pouco mais grave
            idx = np.arange(0, len(x) - 1, 0.85)
            x = np.interp(idx, np.arange(len(x)), x) * 0.9
        i0 = int((t + rnd.uniform(-0.018, 0.018)) * sr)
        if i0 < 0:
            continue
        out[i0:i0 + len(x)] += x[: max(0, len(out) - i0)]
    if not out.any():
        return None
    out *= 0.5 / (np.abs(out).max() + 1e-9)
    CACHE.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", str(arq)],
                   input=out.tobytes(), check=True)
    return arq


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
         "chuva": roteiro.get("chuva", 0), "grao": roteiro.get("grao", 0.16), "cintilar": roteiro.get("cintilar", 0),
         "vigia_padrao": roteiro.get("vigia_padrao", True),  # False: Vigia só nas cenas com "com_vigia"/"vigia"
         "cenas": [], "poses": [], "legendas": [], "escuros": []}
    plano = {"ambientes": [], "musica": roteiro.get("musica"), "trilhas": [], "efeitos": [], "abafar": [], "quedas": [],
             # com vinheta final, a música-assinatura toca até o último quadro (some junto com a imagem)
             "fim_musica": (duracao - 0.3) if any(b.get("cta_inicio") for b in roteiro["batidas"]) else rel.t[-1][1]}
    for amb in roteiro.get("ambiente_inicial", []):
        plano["ambientes"].append({"t": 0.0, **amb})
    ab = roteiro.get("abertura")
    if ab and ab.get("imagem") and not (base / ab["imagem"]).exists() and (base / "provisorias" / Path(ab["imagem"]).name).exists():
        ab = dict(ab, imagem="provisorias/" + Path(ab["imagem"]).name)
    if ab and ab.get("antes_da_batida"):
        kb = ab["antes_da_batida"]
        t_a0, t_a1 = rel.fim(kb - 1) + 0.3 + ab.get("segurar", 0), rel.inicio(kb) - 0.3  # "segurar": a cena anterior fica
        if ab.get("texto"):  # cartão de título desenhado (sem imagem)
            D["_abertura_meio"] = {"t0": t_a0, "tipo": "texto", "texto": ab["texto"], "vermelho": ab.get("vermelho", "PERTO."),
                                   "tamanho": ab.get("tamanho", 84), "peso": 800, "fonte": "Anton", "cps": 40,
                                   "relampagos": ab.get("relampagos", [0.15]), "abertura": True}
        else:
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
            c = json.loads(json.dumps(c))
            # 12/11 (Ep. 08): kanji/texto japonês SOBRE a imagem (pincel, mesclado à figura). "em": palavra → "t" (s)
            if c.get("kanji"):
                c["kanji"] = [c["kanji"]] if isinstance(c["kanji"], dict) else c["kanji"]
                for kj in c["kanji"]:
                    if kj.get("em"):
                        kj["t"] = rel.em(k, kj.pop("em"))
            if not D["cenas"]:
                c["t0"] = 0.0
            elif D["cenas"][-1].get("abertura") and len(D["cenas"]) == 1:
                c.pop("em", None); c["t0"] = D["abertura_fim"]
            else:
                c["t0"] = fronteira(rel, rel.indice(k, c.pop("em", None)))
                # saída lenta de cena tensa: a transição começa ANTES, dentro do silêncio, e termina quando a voz volta
                if c.get("antecipar") and D["cenas"]:
                    c["t0"] = max(D["cenas"][-1]["t0"] + 0.5, c["t0"] - float(c["antecipar"]))
            # 12/11 (Ep. 08): chat (mensagens presas a palavras), mapa (ponto some numa palavra), relógios
            for m in c.get("mensagens", []):
                m["t"] = rel.em(k, m.pop("em")) if m.get("em") else c["t0"] + float(m.get("apos", 0))
                if m.get("digitando"):
                    m["digitando_de"], m["digitando_ate"] = m["t"] - float(m["digitando"]), m["t"]
                if m.get("imagem"):
                    m["imagem"] = str((base / m["imagem"]).resolve())
            for lado in c.get("lados", []):
                if lado.get("imagem"):
                    lado["imagem"] = str((base / lado["imagem"]).resolve())
            if c.get("some_em"):
                c["some"] = rel.em(k, c.pop("some_em")) - c["t0"]
            if c.get("video"):  # cena com vídeo curto: os quadros são extraídos depois que a duração da cena é conhecida
                c["video"] = str((base / c["video"]).resolve())
                if not Path(c["video"]).exists():
                    raise SystemExit(f"vídeo não encontrado: {c['video']}")
                D["cenas"].append(c)
                continue
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
            if c.get("revelar") and c["revelar"].get("clara"):
                c["revelar"]["clara"] = str((base / c["revelar"]["clara"]).resolve())
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
    pp = roteiro.get("preencher_pausas")
    if pp:
        D["cenas"].sort(key=lambda c: c["t0"])
        inis = [c["t0"] for c in D["cenas"]]
        novas = []
        for i in range(len(rel.t) - 1):
            g0, g1 = rel.t[i][1], rel.t[i + 1][0]
            if g1 - g0 < pp.get("min", 1.3):
                continue
            # cena em vigor no meio da pausa
            k = max(j for j, t in enumerate(inis) if t <= g0 + 0.05) if any(t <= g0 + 0.05 for t in inis) else None
            if k is None:
                continue
            c = D["cenas"][k]
            prox = inis[k + 1] if k + 1 < len(inis) else 1e9
            if not c.get("imagem") or c.get("video") or c.get("vigia") or c.get("tipo") or c.get("revelar") or c.get("abertura"):
                continue
            if g0 - c["t0"] < 1.0 or prox - g1 < 0.4:  # perto de um corte: não corta de novo
                continue
            n = dict(c)
            z0 = c.get("zoom", [1.0, 1.05])[1]
            f1 = c.get("foco", [[0.5, 0.5], [0.5, 0.5]])[1]
            n["zoom"] = [z0 * 1.14, z0 * 1.19] if z0 < 1.25 else [max(1.0, z0 * 0.86), max(1.0, z0 * 0.84)]
            n["foco"] = [list(f1), [f1[0], f1[1] - 0.02]]
            n["t0"] = g0 + min(0.35, (g1 - g0) / 3)
            novas.append(n)
        D["cenas"] += novas
        print(f"    pausas preenchidas com novo enquadramento: {len(novas)}")
    D["cenas"].sort(key=lambda c: c["t0"])
    for i, c in enumerate(D["cenas"]):
        c["t1"] = D["cenas"][i + 1]["t0"] if i + 1 < len(D["cenas"]) else duracao
    for c in D["cenas"]:
        if c.get("video"):
            extrair_quadros(c, fps)
    # 10/11: tela de texto precisa ficar INTEIRA na tela tempo suficiente para ler ("20 MINUTOS" sumia antes)
    for c in D["cenas"]:
        txt = (c.get("texto") or "").strip()
        if c.get("tipo") == "texto" and txt and not c.get("abertura"):
            pronto = 0.25 + len(txt) / (c.get("cps") or 22)
            visivel = (c["t1"] - c["t0"]) - pronto
            precisa = 1.5 + 0.3 * len(txt.split())
            if visivel < precisa:
                print(f"    aviso leitura: \"{txt[:40]}\" fica inteiro só {visivel:.1f} s (precisa {precisa:.1f} s)")
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
        k_cta = next((k for k, b in enumerate(roteiro["batidas"]) if b.get("cta_inicio")), None)
        if k_cta is not None:  # vinheta falada: a tela final começa junto da fala de inscrição
            t_cta = max(0.0, rel.inicio(k_cta) - cta.get("antes", 0.8))
        D["cta"] = {"t0": t_cta, "titulo": cta.get("titulo"), "canal": cta.get("canal"), "subtitulo": cta.get("subtitulo")}
        if k_cta is not None and cta.get("clique_em"):  # o botão é clicado quando o Vigia diz a palavra
            D["cta"]["clique"] = round(rel.em(k_cta, cta["clique_em"]) - t_cta, 2)
        if cta.get("fundo"):  # chamada final no cenário do Vigia, com ele em destaque
            D["cenas"].append({"t0": t_cta, "t1": duracao, "imagem": str((base / cta["fundo"]).resolve()),
                               "zoom": [1.0, 1.04], "foco": [[0.5, 0.5], [0.5, 0.5]], "vigia": True, "lado": "esq",
                               "encaixe": "cobrir"})
            D["cenas"].sort(key=lambda c: c["t0"])
            for i, c in enumerate(D["cenas"][:-1]):
                c["t1"] = D["cenas"][i + 1]["t0"]
        plano["efeitos"] += [{"t": t_cta, "som": "whoosh", "volume_db": -10},
                             {"t": t_cta + D["cta"].get("clique", 1.35), "som": "tecla", "volume_db": -2}]
        if cta.get("pose"):
            D["poses"].append({"t": t_cta + 0.2, "pose": cta["pose"], "tipo": "enfase", "segurar": 9})
    # som de digitação nas telas de texto (uma tecla por letra, no mesmo ritmo do texto na tela)
    for c in D["cenas"]:
        if c.get("tipo") == "texto" and roteiro.get("som_digitacao", True):
            arq = trilha_digitacao(c, c.get("t1", c["t0"] + 5) - c["t0"])
            if arq:
                # 10/11: digitação com entrada suave (o volume -26 foi o escolhido pelo usuário no Ep. 03)
                base_db = roteiro.get("digitacao_db", -26)
                plano["efeitos"].append({"t": c["t0"], "arquivo": str(arq), "som": "digitacao", "entrada": 0.4,
                                         "volume_db": base_db + 3 if c.get("estilo") == "impacto" else base_db})
    D["poses"].sort(key=lambda p: p["t"])
    if any(p.get("grupo") == "conversa" for p in av["poses"].values()):
        D["poses"] = poses_de_conversa(D["poses"], rel, av["poses"], roteiro, duracao)
    dest = [norm(w) for w in leg.get("destaques", [])]
    sem = set()
    for kb, b in enumerate(roteiro["batidas"]):
        if b.get("sem_legenda"):
            a0, a1 = rel.faixas[kb]
            sem.update(range(a0, a1))
    for bl in blocos_legenda(rel, leg.get("max_caracteres", 26 if H > W else 42)):
        if any(abs(bl["t0"] - (rel.t[i][0] - 0.05)) < 0.02 for i in sem):
            continue
        bl["destaques"] = dest
        D["legendas"].append(bl)
    return D, plano


# Hierarquia (estudo 09/11): VOZ > efeitos-chave > trilha > ambiente. A trilha fica presente nos respiros e
# abaixa ~6–8 dB quando a voz fala; efeitos que caem em cima da fala também abaixam; ambiente nunca é amplificado.
MIX_PADRAO = {"musica_ganho_db": 0.0, "ambiente_ganho_db": 0.0, "efeitos_ganho_db": 0.0,
              "ducking": "threshold=0.025:ratio=3.5:attack=40:release=650:knee=4",
              "ducking_efeitos": "threshold=0.03:ratio=3:attack=15:release=400:knee=4",
              "sem_sustos": True, "entrada_efeitos": 0.25}  # padrão da série: tensão sem sons altos do nada


def _ler(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "2", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def _env_db(a, sr=48000, janela=0.05):
    q = int(sr * janela)
    k = len(a) // q
    m = (a[:k * q] ** 2).reshape(k, q).mean(axis=1)
    return 10 * np.log10(m + 1e-12)


def _suavizar(g, ataque, soltura):
    out, v = np.empty_like(g), g[0]
    for i, x in enumerate(g):
        v = v + (x - v) * (ataque if x < v else soltura)  # desce rápido, sobe devagar
        out[i] = v
    return out


def automixar(stem, saida, mix):
    """Mixagem por regras (estudo 09/11): a voz manda. Enquanto o narrador fala, a trilha fica
    `fundo_sob_voz` dB abaixo da voz e os efeitos no máximo `efeitos_sob_voz` dB abaixo; nos respiros
    (sem voz) trilha e efeitos voltam ao volume cheio — é ali que a tensão aparece."""
    alvo_b = mix.get("fundo_sob_voz", -12.0)
    alvo_e = mix.get("efeitos_sob_voz", -4.0)
    v, b, e = _ler(stem["voz"]), _ler(stem["fundo"]), _ler(stem["efeitos"])
    n = min(len(v), len(b), len(e))
    v, b, e = v[:n], b[:n], e[:n]
    jan = 0.05
    ev = _env_db(v.mean(1), janela=jan)
    # voz "ativa": nível suavizado com segurança de 0,35 s antes e 0,5 s depois
    fala = ev > -42
    pre, pos = int(0.35 / jan), int(0.5 / jan)
    ativa = fala.copy()
    for i in np.nonzero(fala)[0]:
        ativa[max(0, i - pre):i + pos] = True
    nivel_voz = np.convolve(np.where(fala, ev, -90), np.ones(20) / 20, mode="same")  # ~1 s
    nivel_voz = np.maximum(nivel_voz, np.median(ev[fala]) - 6) if fala.any() else nivel_voz
    def ganho(stem_a, alvo):
        eb = _env_db(stem_a.mean(1), janela=jan)
        eb_s = np.convolve(eb, np.ones(6) / 6, mode="same")  # 0,3 s
        g = np.where(ativa, np.minimum(0.0, (nivel_voz + alvo) - eb_s), 0.0)
        g = _suavizar(g, 0.5, 0.06)
        g = np.repeat(10 ** (g / 20), int(48000 * jan))
        return np.pad(g, (0, max(0, n - len(g))), constant_values=1.0)[:n, None]
    gb, ge = ganho(b, alvo_b), ganho(e, alvo_e)
    # teto nos silêncios: nenhum susto/trilha passa de (voz típica + margem) — evita estouro tipo trovão
    voz_tipica = float(np.median(ev[fala])) if fala.any() else -20.0
    def teto(stem_a, g_atual, margem):
        eb = _env_db((stem_a * g_atual).mean(1), janela=jan)
        eb_s = np.maximum(eb, np.convolve(eb, np.ones(3) / 3, mode="same"))
        g = np.minimum(0.0, (voz_tipica + margem) - eb_s)
        g = _suavizar(g, 0.7, 0.08)
        g = np.repeat(10 ** (g / 20), int(48000 * jan))
        return np.pad(g, (0, max(0, n - len(g))), constant_values=1.0)[:n, None]
    # "sem_sustos" (padrão da série desde 09/11): nada passa da voz, nem nos silêncios — tensão, não susto barulhento
    suave = mix.get("sem_sustos", False)
    gb = gb * teto(b, gb, mix.get("fundo_pico_max", -6.0 if suave else -3.0))
    # 10/11: efeitos nos silêncios no máximo 8 dB abaixo da voz típica (com -3 os sub_drops do Ep. 04 ainda
    # "socavam" depois de um silêncio). O grave fica como vibração, não como pancada.
    ge = ge * teto(e, ge, mix.get("efeitos_pico_max", -8.0 if suave else 2.0))
    b, e = b * gb, e * ge
    for k, a in (("fundo", b), ("efeitos", e)):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", "-", stem[k]],
                       input=a.astype(np.float32).tobytes(), check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", "48000", "-ac", "2", "-i", "-", saida],
                   input=(v + b + e).astype(np.float32).tobytes(), check=True)


def relatorio_mix(stem, duracao):
    """Mede, a cada 2 s, o fundo e os efeitos em relação à voz e avisa onde eles encobrem o narrador."""
    jan = 0.5
    v, b, e = (_env_db(_ler(stem[k]).mean(1), janela=jan) for k in ("voz", "fundo", "efeitos"))
    k = min(len(v), len(b), len(e))
    v, b, e = v[:k], b[:k], e[:k]
    fala = v > -36
    rel_b, rel_e = (b - v)[fala], (e - v)[fala]
    print(f"    mix (com voz): fundo {np.median(rel_b):+.1f} dB da voz (pior {rel_b.max():+.1f}); "
          f"efeitos pior {rel_e.max():+.1f} dB")
    for i in np.nonzero(fala)[0]:
        if b[i] - v[i] > -7 or e[i] - v[i] > -1:
            print(f"    aviso mix: {i * jan:.1f}s fundo {b[i] - v[i]:+.1f} dB / efeitos {e[i] - v[i]:+.1f} dB da voz")


def saltos(arquivos, limite_db=9.0):
    """Procura sons altos "do nada": momentos em que o som (janela de 0,4 s) sobe mais de `limite_db`
    acima do nível dos 3 s anteriores. Mede só trilha + efeitos (a voz voltando depois de um silêncio é fala, não susto)."""
    lidos = [_ler(x).mean(1) for x in arquivos]
    k = min(len(x) for x in lidos)
    a = sum(x[:k] for x in lidos)
    jan = 0.1
    ev = _env_db(a, janela=jan)
    m = np.convolve(ev, np.ones(4) / 4, mode="same")  # 0,4 s
    achou = []
    for i in range(30, len(m)):
        base = np.median(m[i - 30:i])
        if m[i] > -30 and m[i] - max(base, -45) > limite_db and (not achou or i * jan - achou[-1] > 2):
            achou.append(i * jan)
    for t in achou:
        print(f"    aviso salto: {t:.1f}s sobe mais de {limite_db:.0f} dB de repente")
    return achou


# ---------------------------------------------------------------------------------------------------------
# 11/11 — "worldizing": a fala de um personagem ganha o som do LUGAR de onde ela vem (atrás da porta, no
# telefone). O narrador continua sendo o mesmo; o ouvido é que passa a saber onde a voz está. A duração de
# cada trecho não muda (afinação por rubberband, sem mexer no tempo) — as pausas e a sincronia ficam intactas.
VOZ_FX = {
    # madeira maciça entre a voz e o ouvido: some o agudo, sobra o corpo; reflexo curto de corredor
    "porta": "highpass=f=140,lowpass=f=2100,lowpass=f=2600,equalizer=f=320:t=q:w=1.0:g=3,"
             "aecho=0.85:0.75:38|71|113:0.30|0.20|0.12,volume=3dB",
    # alto-falante de celular: só a faixa da telefonia, um pouco saturada
    "telefone": "highpass=f=380,highpass=f=380,lowpass=f=3200,lowpass=f=3200,equalizer=f=1800:t=q:w=1.2:g=4,"
                "acompressor=threshold=-24dB:ratio=6:attack=2:release=60:makeup=3,volume=2dB",
}


def tratar_vozes(voz, batidas, tempos, destino):
    """Batida com "voz_fx": {"tipo": "porta"|"telefone", "tom": 0.84, "de": "palavra"} — processa só aquele
    trecho da narração (do começo da batida, ou da palavra "de", até o fim da batida) e devolve o novo wav."""
    import numpy as np
    pedidos, i0 = [], 0
    for b in batidas:
        pal = tokens(b["fala"])
        fx = b.get("voz_fx")
        if fx:
            fx = {"tipo": fx} if isinstance(fx, str) else fx
            k = next((j for j, w in enumerate(pal) if fx.get("de") and w.startswith(norm(fx["de"]))), 0)
            pedidos.append((tempos[i0 + k][0], tempos[i0 + len(pal) - 1][1], fx))
        i0 += len(pal)
    if not pedidos:
        return voz
    sr = 48000
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(voz), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32).copy()
    for t0, t1, fx in pedidos:
        x0, x1 = max(0, int((t0 - 0.12) * sr)), min(len(a), int((t1 + 0.35) * sr))
        cadeia = VOZ_FX[fx["tipo"]]
        if fx.get("tom") and abs(fx["tom"] - 1) > 0.01:      # voz "grossa, arrastada": mais grave, mesmo tempo
            cadeia = f"rubberband=pitch={fx['tom']}:formant=shifted," + cadeia
        y = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                                          "-af", cadeia, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                                         input=a[x0:x1].tobytes(), capture_output=True, check=True).stdout, np.float32)
        n = x1 - x0
        y = np.pad(y, (0, max(0, n - len(y))))[:n]
        r = int(0.04 * sr); g = np.ones(n, np.float32); g[:r] = np.linspace(0, 1, r); g[-r:] = np.linspace(1, 0, r)
        a[x0:x1] = a[x0:x1] * (1 - g) + y * g                 # emenda suave: sem clique na entrada/saída
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", str(destino)],
                   input=a.tobytes(), check=True)
    print(f"    falas com som de lugar (porta/telefone): {len(pedidos)}")
    return destino


def mixar_cenas(voz_wav, inicio_voz, duracao, plano, saida, mix=None, sem_voz=False):
    mix = {**MIX_PADRAO, **(mix or {})}
    sons = AQUI / "sons"
    ent = ["-i", str(voz_wav)]
    # "voz_pro": cadeia de locução de estúdio — tira o embolado (300 Hz), dá corpo (120 Hz) e presença (3,5 kHz),
    # doma o "s" e comprime em dois estágios leves (mais natural que um estágio forte)
    cadeia_voz = ("highpass=f=80,equalizer=f=120:t=q:w=0.9:g=1.5,equalizer=f=300:t=q:w=1.2:g=-2.5,"
                  "equalizer=f=3500:t=q:w=1.0:g=2,deesser=i=0.35:m=0.5:f=0.5,"
                  "acompressor=threshold=-24dB:ratio=2:attack=12:release=200:makeup=1.5,"
                  "acompressor=threshold=-14dB:ratio=3:attack=4:release=120,"
                  if mix.get("voz_pro") else "highpass=f=70,acompressor=threshold=-20dB:ratio=2.2:attack=8:release=180,")
    f = [f"[0:a]aresample=48000,{cadeia_voz}"
         f"adelay={int(inicio_voz * 1000)}:all=1,apad,atrim=0:{duracao:.3f},asplit=4[voz][chave][chave2][vozstem]"]
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
                 f"volume={a.get('volume_db', -6) + mix['ambiente_ganho_db']}dB,afade=t=in:d={fi},afade=t=out:st={max(0, fim - ini - 0.8):.3f}:d=0.8,"
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
                 f"volume={m.get('volume_db', -12) + mix['musica_ganho_db']}dB,afade=t=in:d={fi},afade=t=out:st={max(0, fim - ini - fo):.3f}:d={fo},"
                 f"adelay={int(ini * 1000)}:all=1[mus{n}]")
        camas.append(f"[mus{n}]")
        n += 1
    if not camas:
        f.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{duracao:.3f}[vazio]")
        camas.append("[vazio]")
    cama = "[cama0]"
    # "fundo_bolso": abre um bolso na música onde mora a inteligibilidade da voz (2–4 kHz) — a trilha pode tocar
    # mais presente sem disputar com o narrador (em vez de só abaixar o volume dela)
    bolso = "equalizer=f=2800:t=q:w=0.9:g=-3.5,equalizer=f=1200:t=q:w=1.2:g=-1.5," if mix.get("fundo_bolso") else ""
    f.append(f"{''.join(camas)}amix=inputs={len(camas)}:normalize=0:duration=longest,{bolso}apad,atrim=0:{duracao:.3f}{cama}")
    # automações: som abafado (passa-baixa) e quedas de volume
    cadeia = []
    for a0, a1, _ in plano["abafar"]:
        cadeia.append(f"lowpass=f=650:enable='between(t,{a0:.2f},{a1:.2f})'")
    for q0, q1, forca in plano["quedas"]:
        cadeia.append(f"volume={1 - forca:.2f}:enable='between(t,{q0:.2f},{q1:.2f})'")
    f.append(f"{cama}{','.join(cadeia) if cadeia else 'anull'}[cama1]")
    f.append("[cama1]anull[camad]")
    f.append("[chave]anullsink")
    efs = []
    for e in plano["efeitos"]:
        arq = Path(e["arquivo"]) if e.get("arquivo") else sons / f"{e['som']}.mp3"
        if not arq.exists() or e["t"] >= duracao:
            print(f"  aviso: efeito '{e['som']}' ignorado", file=sys.stderr)
            continue
        ent += ["-i", str(arq)]
        extra = "lowpass=f=900,bass=g=4:f=70," if e.get("grave") else ""
        ent_s = e.get("entrada", mix.get("entrada_efeitos", 0))  # subida suave do efeito (s): sem estalo de susto
        if ent_s:
            extra += f"afade=t=in:d={ent_s},"
        f.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,{extra}volume={e['volume_db'] + mix['efeitos_ganho_db']}dB,"
                 f"adelay={max(0, int(e['t'] * 1000))}:all=1[e{n}]")
        efs.append(f"[e{n}]")
        n += 1
    if efs:
        f.append(f"{''.join(efs)}amix=inputs={len(efs)}:normalize=0:duration=longest,apad,atrim=0:{duracao:.3f}[fx0]")
        f.append("[fx0]anull[fx]")
        f.append("[chave2]anullsink")
    else:
        f.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{duracao:.3f}[fx]")
        f.append("[chave2]anullsink")
    f.append("[camad]asplit=2[camaA][camaB]")
    f.append("[fx]asplit=2[fxA][fxB]")
    f.append(f"[voz][camaA][fxA]amix=inputs=3:normalize=0:duration=first,atrim=0:{duracao:.3f}[mix]")
    bruto = str(saida) + ".bruto.wav"
    stem = {kk: str(saida) + f".{kk}.wav" for kk in ("voz", "fundo", "efeitos")}
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ent, "-filter_complex", ";".join(f),
                    "-map", "[mix]", "-f", "null", "-",
                    "-map", "[vozstem]", stem["voz"], "-map", "[camaB]", stem["fundo"], "-map", "[fxB]", stem["efeitos"]],
                   check=True)
    automixar(stem, bruto, mix)
    relatorio_mix(stem, duracao)
    saltos([stem["fundo"], stem["efeitos"]])
    med = subprocess.run(["ffmpeg", "-i", bruto, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    mm = json.loads(med[med.rfind("{"):med.rfind("}") + 1])
    if sem_voz:  # prévia: mesmo ganho que o vídeo final teria, mas só trilha + efeitos (sem a voz-fantasma)
        ganho = -14.0 - float(mm["input_i"])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", stem["fundo"], "-i", stem["efeitos"], "-filter_complex",
                        f"amix=inputs=2:normalize=0,volume={ganho:.2f}dB,aresample=48000,"
                        "alimiter=limit=0.70:attack=1:release=50:level=disabled", "-ac", "2", saida], check=True)
        os.remove(bruto)
        return
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", bruto, "-af",
                    f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={mm['input_i']}:measured_TP={mm['input_tp']}:"
                    f"measured_LRA={mm['input_lra']}:measured_thresh={mm['input_thresh']}:offset={mm['target_offset']}:"
                    "linear=true,aresample=48000,alimiter=limit=0.70:attack=1:release=50:level=disabled", "-ac", "2", saida], check=True)
    os.remove(bruto)


# ---------------------------------------------------------------- principal
def _duracao_midia(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def extrair_quadros(c, fps):
    """Cena com vídeo: extrai em JPG só os quadros que a cena usa (o navegador carrega um por vez, sem estourar
    a memória). Campos: "video", "video_inicio" (s dentro do clipe), "velocidade" (1 = normal). Se o clipe for
    mais curto que a cena, ele é desacelerado até 0,6× e, se ainda faltar, congela no último quadro (nunca repete:
    loop de vídeo denuncia edição barata). Cache em painel/.cache_quadros."""
    import hashlib
    ini = float(c.get("video_inicio", 0))
    precisa = (c["t1"] - c["t0"]) + 1.2  # margem para a transição de saída
    disp = max(0.1, _duracao_midia(c["video"]) - ini)
    vel = float(c.get("velocidade", 1.0))
    if disp / vel < precisa:
        vel = max(0.6, min(vel, disp / precisa))
    n = int(round(precisa * fps)) + 1
    chave = hashlib.md5(f"{c['video']}|{ini}|{vel:.3f}|{n}|{fps}".encode()).hexdigest()[:16]
    pasta = AQUI / ".cache_quadros" / chave
    if not (pasta / f"{n:05d}.jpg").exists():
        pasta.mkdir(parents=True, exist_ok=True)
        filtro = f"setpts=PTS/{vel:.4f},fps={fps},tpad=stop_mode=clone:stop_duration={precisa + 1:.2f}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.3f}", "-i", c["video"], "-an", "-vf", filtro,
                        "-frames:v", str(n), "-q:v", "3", str(pasta / "%05d.jpg")], check=True)
    c["quadros"] = {"dir": str(pasta), "n": n, "fps": fps}
    c["imagem"] = str(pasta / "00001.jpg")
    if vel < 0.999:
        print(f"    vídeo {Path(c['video']).name}: desacelerado para {vel:.2f}× para cobrir a cena")


def voz_simulada(batidas, destino, ppm=128):
    """Prévia SEM narração (--sem-voz): estima o tempo de cada palavra pelo ritmo do Vigia (Ep. 03: ~128
    palavras/min contando pausas) e grava uma "voz-fantasma" (ruído na faixa da fala, só onde haveria palavra).
    A fantasma serve para a mixagem abaixar/subir a trilha e acertar o volume como no vídeo final; no arquivo
    final ela é retirada (mixar_cenas com sem_voz=True)."""
    sr = 48000
    durs, pausas = [], []
    for b in batidas:
        ws = tokens(b["fala"])
        for j, w in enumerate(ws):
            durs.append(0.08 + 0.068 * len(norm(w)))
            fimb = j == len(ws) - 1
            pz = 0.8 if w.endswith(("…", "...")) else 0.55 if w.endswith((".", "?", "!", '."', '?"')) else \
                0.35 if w.endswith((":", ";")) else 0.22 if w.endswith(",") else 0.04
            pausas.append(pz + (0.2 if fimb else 0))
    total = sum(durs) + sum(pausas)
    k = (len(durs) / ppm * 60) / total
    tempos, t = [], 0.4
    for d, pz in zip(durs, pausas):
        tempos.append((t, t + d * k)); t += (d + pz) * k
    n = int((t + 1) * sr)
    env = np.zeros(n, np.float32)
    for a, e in tempos:
        i0, i1 = int(a * sr), int(e * sr)
        f = min(int(0.03 * sr), (i1 - i0) // 3)
        seg = np.ones(i1 - i0, np.float32)
        if f > 0:
            seg[:f] = np.linspace(0, 1, f); seg[-f:] = np.linspace(1, 0, f)
        env[i0:i1] = seg
    ruido = np.random.default_rng(1).normal(0, 0.14, n).astype(np.float32) * env
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                    "-af", "highpass=f=250,lowpass=f=3500", str(destino)], input=ruido.tobytes(), check=True)
    print(f"    voz simulada: {len(durs)} palavras em {t / 60:.1f} min (ritmo {ppm} palavras/min)")
    return tempos


def gerar(caminho_roteiro, saida, rascunho=False, so_audio=None, sem_voz=False):
    roteiro = json.load(open(caminho_roteiro, encoding="utf-8"))
    roteiro["_pasta"] = str(Path(caminho_roteiro).resolve().parent)
    batidas = roteiro["batidas"]
    texto = "\n".join(b["fala"] for b in batidas)
    print("1/5 narração (Gemini)…")
    if sem_voz:
        print("    PRÉVIA SEM NARRAÇÃO: tempos estimados, só trilha e efeitos no áudio final")
        wav = None
    elif roteiro.get("voz_arquivo"):  # narração já existente (ex.: trecho do episódio longo para um Short)
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
    if sem_voz:
        wav = CACHE / f"voz_fantasma_{os.getpid()}.wav"
        CACHE.mkdir(exist_ok=True)
        tempos, casadas = voz_simulada(batidas, wav), 1.0
        roteiro["apertar_pausas"] = False
    else:
        ouvidas = transcrever(wav, texto)
        tempos, casadas = alinhar(palavras, ouvidas)
        tempos = ajustar_inicios(wav, tempos)
    print(f"    {casadas:.0%} das palavras reconhecidas")
    if casadas < 0.7:
        print("    aviso: narração muito diferente do roteiro (a voz pode ter lido instruções ou pulado trechos)")
    # corta o que vier antes da primeira palavra do roteiro (ex.: instrução de estilo lida em voz alta)
    corte = max(0.0, tempos[0][0] - 0.3)  # folga: o Whisper pode marcar o início da 1ª palavra tarde
    tmp = Path(tempfile.mkdtemp(prefix="painel_"))
    voz_cortada = tmp / "voz_inicio.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{corte:.3f}", "-i", wav, voz_cortada], check=True)
    tempos = [(s - corte, e - corte) for s, e in tempos]
    if "apertar_pausas" not in roteiro and roteiro.get("formato") == "16:9":
        print("    ATENÇÃO: roteiro sem \"apertar_pausas\" — as pausas da narração serão ENCURTADAS (regra da casa: não "
              "encurtar). Ponha \"apertar_pausas\": false se não for isso que você quer.")
    if roteiro.get("apertar_pausas", True):
        antes = tempos[-1][1]
        voz_final = tmp / "voz.wav"
        tempos = apertar_pausas(voz_cortada, palavras, tempos, voz_final, roteiro.get("pausas"))
        voz_cortada = voz_final
        print(f"    pausas encurtadas: {antes:.1f} s -> {tempos[-1][1]:.1f} s")
    # silêncios dramáticos pedidos no roteiro ("pausa_antes_s" na batida) — inseridos depois do aperto
    ab0 = roteiro.get("abertura")
    if ab0 and ab0.get("antes_da_batida") and not batidas[ab0["antes_da_batida"]].get("pausa_antes_s"):
        batidas[ab0["antes_da_batida"]]["pausa_antes_s"] = ab0["duracao"] + ab0.get("segurar", 0) + 0.8
    insercoes, i0 = [], 0
    for b in batidas:
        n_pal = len(tokens(b["fala"]))
        if b.get("pausa_antes_s") and i0 > 0:
            insercoes.append((i0, float(b["pausa_antes_s"])))
        i0 += n_pal
    if insercoes:
        voz_cortada, tempos = inserir_silencios(voz_cortada, tempos, insercoes, tmp / "voz_pausas.wav")
    if not sem_voz:
        voz_cortada = tratar_vozes(voz_cortada, batidas, tempos, tmp / "voz_fx.wav")
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
    if so_audio:  # reaproveita a imagem de um vídeo já pronto e refaz só a mixagem
        print("3/5 quadros: reaproveitando", so_audio)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", so_audio, "-an", "-c:v", "copy", tmp / "video.mp4"], check=True)
    else:
        print(f"3/5 quadros ({duracao:.1f} s)…")
        cmd = ["node", str(AQUI / "render.js"), str(tmp / "linha.json"), str(tmp / "video.mp4")]
        if rascunho:
            cmd.append("--rascunho")
        subprocess.run(cmd, check=True)
    print("4/5 mixagem…")
    if roteiro.get("modo") == "cenas":
        mixar_cenas(voz_cortada, roteiro["_inicio_voz"], duracao, plano, str(tmp / "audio.wav"), roteiro.get("mix"),
                    sem_voz=sem_voz)
    else:
        mixar(voz_cortada, VOZ0, duracao, eventos, roteiro.get("trilha"), str(tmp / "audio.wav"))
    print("5/5 finalizando…")
    venc = ["-c:v", "copy"] if so_audio else ["-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "10M",
                                              "-bufsize", "20M", "-pix_fmt", "yuv420p"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp / "video.mp4", "-i", tmp / "audio.wav", *venc,
                    "-c:a", "aac", "-b:a", "256k", "-aac_is", "0", "-aac_ms", "0", "-aac_pns", "0",  # 10/11: o estéreo de intensidade do AAC distorcia o canal direito (+6 dB)
 "-shortest", "-movflags", "+faststart", saida], check=True)
    json.dump({"palavras": [(w, round(s, 2), round(e, 2)) for w, (s, e) in zip(palavras, rel.t)],
               "poses": [(round(p["t"], 2), p["pose"], p.get("tipo")) for p in D.get("poses", [])]},
              open(str(saida) + ".tempos.json", "w"), ensure_ascii=False)
    if not os.environ.get("MANTER_TEMP"):  # 10/11: cada render deixava 1,5–2,5 GB em /tmp e o disco encheu
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"pronto: {saida}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    so = next((x.split("=", 1)[1] for x in sys.argv if x.startswith("--so-audio=")), None)
    gerar(a[0], a[1], rascunho="--rascunho" in sys.argv, so_audio=so, sem_voz="--sem-voz" in sys.argv)
