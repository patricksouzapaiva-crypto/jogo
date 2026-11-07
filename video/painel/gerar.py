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
    prompt = f"{estilo}:\n\n{texto}"
    chave = hashlib.sha1(f"{modelo}|{nome}|{prompt}".encode()).hexdigest()[:16]
    wav = CACHE / f"voz_{chave}.wav"
    if wav.exists():
        return wav
    CACHE.mkdir(exist_ok=True)
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
        headers={"x-goog-api-key": os.environ.get("GEMINI_API_KEY", "proxy")},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"responseModalities": ["AUDIO"],
                                   "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": nome}}}}},
        timeout=600)
    r.raise_for_status()
    parte = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
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


# ---------------------------------------------------------------- tempo das palavras (Whisper)
def transcrever(wav: Path, roteiro_txt: str):
    from faster_whisper import WhisperModel
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language="pt", word_timestamps=True, initial_prompt=roteiro_txt[:200])
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


def apertar_pausas(wav: Path, palavras, tempos, destino: Path, limites=(0.42, 0.24, 0.12)):
    """Encurta silêncios longos entre palavras (só encurta, nunca alonga).
    limites = pausa máxima depois de ponto final, de vírgula e entre palavras comuns."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    sr, pedacos, novos, cursor, desloc = 48000, [], [], 0.0, 0.0
    cortes = []  # (inicio, fim) de trechos a remover
    for i in range(len(tempos) - 1):
        fim_i, ini_j = tempos[i][1], tempos[i + 1][0]
        w = palavras[i]
        lim = limites[0] if w[-1] in ".!?…" else limites[1] if w[-1] in ",;:—" else limites[2]
        if ini_j - fim_i > lim + 0.05:
            meio = lim / 2
            cortes.append((fim_i + meio, ini_j - meio))
    for c0, c1 in cortes:
        pedacos.append(a[int(cursor * sr):int(c0 * sr)])
        cursor = c1
    pedacos.append(a[int(cursor * sr):])
    # pequenas rampas nas emendas para não estalar
    f = int(0.008 * sr)
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
                    "linear=true,aresample=48000", "-ac", "2", saida], check=True)
    os.remove(bruto)


# ---------------------------------------------------------------- principal
def gerar(caminho_roteiro, saida, rascunho=False):
    roteiro = json.load(open(caminho_roteiro, encoding="utf-8"))
    roteiro["_pasta"] = str(Path(caminho_roteiro).resolve().parent)
    batidas = roteiro["batidas"]
    texto = "\n".join(b["fala"] for b in batidas)
    print("1/5 narração (Gemini)…")
    wav = narrar(texto, roteiro.get("voz", {}), CACHE)
    print("2/5 tempo das palavras (Whisper)…")
    palavras = [w for b in batidas for w in tokens(b["fala"])]
    ouvidas = transcrever(wav, texto)
    tempos, casadas = alinhar(palavras, ouvidas)
    print(f"    {casadas:.0%} das palavras reconhecidas")
    if casadas < 0.7:
        print("    aviso: narração muito diferente do roteiro (a voz pode ter lido instruções ou pulado trechos)")
    # corta o que vier antes da primeira palavra do roteiro (ex.: instrução de estilo lida em voz alta)
    corte = max(0.0, tempos[0][0] - 0.12)
    tmp = Path(tempfile.mkdtemp(prefix="painel_"))
    voz_cortada = tmp / "voz_inicio.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{corte:.3f}", "-i", wav, voz_cortada], check=True)
    tempos = [(s - corte, e - corte) for s, e in tempos]
    if roteiro.get("apertar_pausas", True):
        antes = tempos[-1][1]
        voz_final = tmp / "voz.wav"
        tempos = apertar_pausas(voz_cortada, palavras, tempos, voz_final)
        voz_cortada = voz_final
        print(f"    pausas encurtadas: {antes:.1f} s -> {tempos[-1][1]:.1f} s")
    rel = Relogio(batidas, tempos, VOZ0)
    fim_voz = rel.t[-1][1]
    duracao = round(fim_voz + roteiro.get("cauda", 1.6), 2)
    D, eventos = montar(roteiro, rel, duracao)
    (tmp / "linha.json").write_text(json.dumps(D, ensure_ascii=False))
    print(f"3/5 quadros ({duracao:.1f} s)…")
    cmd = ["node", str(AQUI / "render.js"), str(tmp / "linha.json"), str(tmp / "video.mp4")]
    if rascunho:
        cmd.append("--rascunho")
    subprocess.run(cmd, check=True)
    print("4/5 mixagem…")
    mixar(voz_cortada, VOZ0, duracao, eventos, roteiro.get("trilha"), str(tmp / "audio.wav"))
    print("5/5 finalizando…")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp / "video.mp4", "-i", tmp / "audio.wav", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida], check=True)
    json.dump({"palavras": [(w, round(s, 2)) for w, (s, _) in zip(palavras, rel.t)]},
              open(str(saida) + ".tempos.json", "w"), ensure_ascii=False)
    print(f"pronto: {saida}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    gerar(a[0], a[1], rascunho="--rascunho" in sys.argv)
