"""Ep. 12 (24/11, pedido do usuário): referência ao Ep. 08 na abertura das REGRAS. Grava só as frases novas com a mesma
voz (o TTS recebe as 2 frases anteriores como contexto e o Whisper acha onde o texto novo começa), e encaixa o trecho na
narração final logo depois de "Ele quer que você siga a regra." (no meio do silêncio). Depois: alinhar.py.
Uso: python3 inserir_ep08.py"""
import json, os, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np, soundfile as sf

AQUI = Path(__file__).parent; A = AQUI / "audio"
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
NOVO = ("Se você viu o nosso episódio sobre o terror japonês, você já ouviu isso de mim: no Japão, o medo é uma regra. "
        "E regra… não tem pena de ninguém. Mas com os yokais é diferente. Aqui, a regra é a única coisa que pode te salvar.")
CONTEXTO = "Agora, se um iôcai não quer a sua alma… o que ele quer? Ele quer que você siga a regra."
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())


def palavras(wav):
    from faster_whisper import WhisperModel
    m = WhisperModel("small", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    seg, _ = m.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    return [(norm(w.word).strip(), w.start, w.end) for s in seg for w in s.words]


bruto = A / "ep08_ref_bruto.wav"
if not bruto.exists():
    (A / "ep08_ref.txt").write_text(CONTEXTO + "\n\n" + NOVO + "\n")
    subprocess.run([sys.executable, str(FERR), str(A / "ep08_ref.txt"), str(bruto)], env={**os.environ, "VOZ": "Algenib"}, check=True)
ws = palavras(bruto)
k = next(i for i in range(1, len(ws) - 3) if [w[0] for w in ws[i:i + 3]] == ["se", "voce", "viu"])
print("ouvido:", " ".join(w[0] for w in ws[k:]))
x, sr = sf.read(bruto, dtype="float32")
if x.ndim > 1: x = x.mean(1)
c0 = (ws[k - 1][2] + ws[k][1]) / 2; c1 = ws[-1][2] + 0.35
seg = x[int(c0 * sr):int(c1 * sr)]
# 24 kHz → 48 kHz e a mesma limpeza da narração (afftdn)
tmp = A / "_ref_seg.wav"; sf.write(tmp, seg, sr)
seg48 = A / "_ref_seg48.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af", "afftdn=nr=12:nf=-50,afade=t=in:d=0.02,areverse,afade=t=in:d=0.08,areverse",
                "-ar", "48000", "-ac", "1", str(seg48)], check=True)
y, sr2 = sf.read(seg48, dtype="float32")
voz, sr3 = sf.read(A / "voz_com_vinheta_limpa.wav", dtype="float32")
mono = voz.ndim == 1
v = voz if mono else voz.mean(1)
# onde termina "regra." da fala 110: pelo alinhamento atual
import falas as F
sys.path.insert(0, str(AQUI.parents[1] / "painel"))
from gerar import tokens
fl = F.ler()[0]; ali = json.load(open(A / "alinhamento.json"))
fim110 = ali[sum(len(tokens(f)) for f in fl[:111]) - 1][1]; ini111 = ali[sum(len(tokens(f)) for f in fl[:111])][0]
corte = fim110 + min(0.5, (ini111 - fim110) / 2)
# mesmo volume da voz em volta
viz = v[int((corte - 8) * sr3):int((corte + 8) * sr3)]
rms = lambda a: np.sqrt(np.mean(a[np.abs(a) > 0.02] ** 2)) if np.any(np.abs(a) > 0.02) else 1e-3
y *= rms(viz) / rms(y)
pausa = np.zeros(int(0.55 * sr3), np.float32)
ins = np.concatenate([pausa, y, pausa])
if not mono: ins = np.stack([ins] * voz.shape[1], 1)
i = int(corte * sr3)
sf.write(A / "voz_com_vinheta_limpa.wav", np.concatenate([voz[:i], ins, voz[i:]]), sr3)
print(f"inserido em {corte:.2f}s: {len(ins) / sr3:.1f}s")
for f in (tmp, seg48): f.unlink()
