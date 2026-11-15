"""Narração do Ep. 09 v4 (15/11): só o que é NOVO vai para o TTS; o resto reaproveita a narração v3 já aprovada
(mesmo timbre, Algenib, gemini-3.8-flash-tts).
- Novo: TEMA reescrito + CAPÍTULOS 1–3 + APARTE ("historia", em 2 pedaços) e o trecho novo do FECHO.
- Velho: o GANCHO (começo do bloco1 v3) e tudo do "O RAFA — 1" em diante (blocos 1–5 v3).
Como no refazer_blocos.py: cada pedaço novo vai ao TTS com as 3 últimas frases do trecho anterior na frente (ele
continua no mesmo tom), e o Whisper acha onde o texto novo começa para cortar o contexto fora.
Saída: audio/bloco1.wav (gancho + história + rafa 1…), audio/bloco5.wav (com o fecho novo); os v3 ficam em
audio/v3/. Depois: python3 narrar.py (junta) → alinhar → trocar_vozes → …
Uso: python3 narrar_v4.py            (gera o que falta; --reusar não chama o TTS se o bruto já existe)"""
import os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
import falas as F

AQUI = Path(__file__).parent; A = AQUI / "audio"; V3 = A / "v3"; V3.mkdir(exist_ok=True)
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
SR = 24000
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
modelo = WhisperModel("small", compute_type="int8")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
PRON = {"han.": "rân.", "*han*": "rân", " han ": " rân ", "Miryang": "Miriâng", "bunshinsaba": "bun-shin-sabá",
        "cheonyeo gwishin": "tchônhô gúishin", "dalgyal gwishin": "talguiál gúishin", "Jeonseol-ui Gohyang": "Djônsôri Gô-hiâng",
        "Wol-ha": "Uól-rá", "Janghwa": "Djang-uá", "Hongryeon": "Rong-riôn", "Cheolsan": "Tchól-san", "Exhuma": "Éksuma"}


def tts_texto(frases):
    t = " ".join(EMOJI.sub("", F.para_tts(f)).strip() for f in frases)
    for a, b in PRON.items():
        t = t.replace(a, b)
    return t.replace("*", "")


def palavras(wav):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    seg, _ = modelo.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    return [(norm(w.word).strip(), w.start, w.end) for s in seg for w in s.words]


def ler(w):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, np.float32).copy()


def achar(ws, alvo, depois=0.0):
    """Início (s) da primeira ocorrência das palavras `alvo` (3 primeiras; se não achar, 2) depois de `depois`."""
    alvo = norm(alvo).split()
    for n in (3, 2):
        for i in range(len(ws) - n):
            if ws[i][1] >= depois and [w[0] for w in ws[i:i + n]] == alvo[:n]:
                return i
    # o Whisper troca número por algarismo ("cem" → "100"): procura a 2ª–4ª palavras e volta uma
    for i in range(1, len(ws) - 3):
        if ws[i][1] >= depois and [w[0] for w in ws[i:i + 3]] == alvo[1:4]:
            return i - 1
    return None


def gerar(nome, contexto, texto):
    """TTS de `texto` com `contexto` na frente; devolve o áudio só do texto novo (o contexto cortado)."""
    bruto = A / f"v4_{nome}_bruto.wav"
    if not ("--reusar" in sys.argv and bruto.exists()):
        ent = A / f"v4_{nome}.txt"; ent.write_text(contexto + "\n\n" + texto + "\n")
        for _ in range(4):
            r = subprocess.run([sys.executable, str(FERR), str(ent), str(bruto)], env={**os.environ, "VOZ": "Algenib"})
            if r.returncode == 0 and bruto.exists():
                break
        else:
            sys.exit(f"{nome}: TTS falhou (cota?)")
    ws = palavras(bruto); k = achar(ws, texto)
    if k is None:
        sys.exit(f"{nome}: não achei o começo ({texto[:40]}) em: {' '.join(w[0] for w in ws[:60])}")
    x = ler(bruto); c0 = int((ws[k - 1][2] + (ws[k][1] - ws[k - 1][2]) * 0.5) * SR) if k else 0
    y = x[c0:]; v = np.where(np.abs(y) > 0.01)[0]; y = y[: v[-1] + int(0.5 * SR)]
    f = int(0.03 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    print(f"{nome}: {len(y) / SR:.1f}s; ouvido: {' '.join(w[0] for w in ws[k:k + 12])} …", flush=True)
    return y


def gravar(x, arq):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le", str(arq)],
                   input=np.clip(x, -1, 1).astype(np.float32).tobytes(), check=True)


rms = lambda y: float(np.sqrt((y[np.abs(y) > 0.01] ** 2).mean()))
pausa = lambda s: np.zeros(int(s * SR), np.float32)
fl, pers, sec, pausas, _ = F.ler()
for b in (1, 5):
    if not (V3 / f"bloco{b}.wav").exists():
        shutil.copy(A / (f"bloco{b}_antes_fecho.wav" if b == 5 and (A / "bloco5_antes_fecho.wav").exists() else f"bloco{b}.wav"), V3 / f"bloco{b}.wav")

# 1) bloco 1: GANCHO (v3) + história nova (2 pedaços) + do "O Rafa tinha vinte e sete anos" em diante (v3)
b1 = ler(V3 / "bloco1.wav"); w1 = palavras(V3 / "bloco1.wav")
k_tema, k_rafa = achar(w1, "Boa noite. Eu sou o Vigia"), achar(w1, "O Rafa tinha vinte e sete anos")
if k_tema is None or k_rafa is None:
    sys.exit("bloco1 v3: não achei o começo do TEMA ou do RAFA 1")
corte_tema = int((w1[k_tema - 1][2] + (w1[k_tema][1] - w1[k_tema - 1][2]) * 0.5) * SR)
corte_rafa = int((w1[k_rafa - 1][2] + (w1[k_rafa][1] - w1[k_rafa - 1][2]) * 0.5) * SR)
gancho = fl[sec["GANCHO"]:sec["TEMA"]]
h1 = fl[sec["TEMA"]:sec["CAPÍTULO 2"]]
h2 = fl[sec["CAPÍTULO 2"]:sec["O RAFA — 1"]]
p1 = gerar("historia1", tts_texto(gancho[-3:]), tts_texto(h1))
p2 = gerar("historia2", tts_texto(h1[-3:]), tts_texto(h2))
ref = rms(b1[:corte_tema]); p1 *= ref / rms(p1); p2 *= ref / rms(p2)
novo1 = np.concatenate([b1[:corte_tema], p1, pausa(1.2), p2, pausa(1.2), b1[corte_rafa:]])
gravar(novo1, A / "bloco1.wav")
print(f"bloco1 v4: {len(novo1) / SR:.1f}s (v3: {len(b1) / SR:.1f}s)")

# 2) bloco 5: FECHO novo entre "Só de noite." e "No conto da Irmã Raposa" (o resto do bloco é o v3)
b5 = ler(V3 / "bloco5.wav"); w5 = palavras(V3 / "bloco5.wav")
k_conto = achar(w5, "No conto da Irmã Raposa")
if k_conto is None:
    sys.exit("bloco5 v3: não achei 'No conto da Irmã Raposa'")
corte5 = int((w5[k_conto - 1][2] + (w5[k_conto][1] - w5[k_conto - 1][2]) * 0.5) * SR)
i0 = next(i for i, f in enumerate(fl) if f.startswith("No Japão, a maldição é uma regra"))
i1 = next(i for i, f in enumerate(fl) if f.startswith("No conto da Irmã Raposa"))
fe = gerar("fecho", tts_texto(fl[i0 - 3:i0]), tts_texto(fl[i0:i1]))
fe *= rms(b5) / rms(fe)
novo5 = np.concatenate([b5[:corte5], fe, pausa(0.6), b5[corte5:]])
gravar(novo5, A / "bloco5.wav")
print(f"bloco5 v4: {len(novo5) / SR:.1f}s (v3: {len(b5) / SR:.1f}s)")
