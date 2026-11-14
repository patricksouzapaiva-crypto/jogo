"""15/11 (pedido do usuário): fecho mais forte — explica o terror coreano (o han), cita lendas mais pesadas (Arang de
Miryang, o fantasma do ovo, o afogado, o bunshinsaba) e pede nos comentários qual o canal deve abrir.
Só o TRECHO NOVO é gerado (o resto do bloco 5 fica igual, mesmo timbre): o TTS recebe as 3 frases anteriores como
contexto, o Whisper acha onde o texto novo começa, e o trecho entra no bloco5.wav entre "Só de noite." e
"No conto da Irmã Raposa". O bloco antigo fica em audio/bloco5_antes_fecho.wav.
Uso: python3 inserir_fecho.py  → audio/bloco5.wav (depois narrar.py para juntar)"""
import os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel
import falas as F

AQUI = Path(__file__).parent; A = AQUI / "audio"
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
SR = 24000
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
modelo = WhisperModel("small", compute_type="int8")
# pronúncia: "han" lido como "rân" (h aspirado coreano), Miryang como "Mi-riâng"
PRON = {"han.": "rân.", "com han": "com rân", "Miryang": "Miriâng", "bunshinsaba": "bun-shin-sabá"}


def palavras(wav):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    seg, _ = modelo.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    return [(norm(w.word).strip(), w.start, w.end) for s in seg for w in s.words]


def ler(w):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), "-ac", "1", "-ar", str(SR), "-f", "f32le",
                                         "-"], capture_output=True, check=True).stdout, np.float32).copy()


fl, *_ = F.ler()
i0 = next(i for i, f in enumerate(fl) if f.startswith("O terror japonês tem regras"))
i1 = next(i for i, f in enumerate(fl) if f.startswith("No conto da Irmã Raposa"))
novo = " ".join(F.para_tts(f) for f in fl[i0:i1])
for a, b in PRON.items():
    novo = novo.replace(a, b)
contexto = "O Rafa nunca mais mandou áudio no grupo. A mãe diz que os dois filhos estão bem. Que a Lívia está ótima. Que come muito. Só de noite."
ent = A / "fecho_novo.txt"; ent.write_text(contexto + "\n\n" + novo + "\n")
bruto = A / "fecho_novo_bruto.wav"
if "--reusar" not in sys.argv or not bruto.exists():
    for t in range(4):
        r = subprocess.run([sys.executable, str(FERR), str(ent), str(bruto)], env={**os.environ, "VOZ": "Algenib"})
        if r.returncode == 0 and bruto.exists():
            break
ws = palavras(bruto)
print("ouvido:", " ".join(w[0] for w in ws))
k = next(i for i in range(len(ws) - 2) if [w[0] for w in ws[i:i + 3]] == ["o", "terror", "japones"])
x = ler(bruto)
c0 = int((ws[k - 1][2] + (ws[k][1] - ws[k - 1][2]) * 0.5) * SR)      # no meio do silêncio antes de "O terror"
trecho = x[c0:]
# corta o silêncio do fim e deixa 0,6 s
v = np.where(np.abs(trecho) > 0.01)[0]; trecho = trecho[: v[-1] + int(0.6 * SR)]
f = int(0.03 * SR); trecho[:f] *= np.linspace(0, 1, f); trecho[-f:] *= np.linspace(1, 0, f)

orig = A / "bloco5_antes_fecho.wav"
if not orig.exists():
    shutil.copy(A / "bloco5.wav", orig)
b5 = ler(orig); wb = palavras(orig)
j = next(i for i in range(len(wb) - 2) if [w[0] for w in wb[i:i + 3]] == ["no", "conto", "da"])
fim_noite, ini_conto = wb[j - 1][2], wb[j][1]
corte = int((fim_noite + (ini_conto - fim_noite) * 0.5) * SR)
pausa = np.zeros(int(0.5 * SR), np.float32)
saida = np.concatenate([b5[:corte], trecho, pausa, b5[corte:]])
# mesmo nível do bloco (RMS das partes faladas)
rms = lambda y: np.sqrt((y[np.abs(y) > 0.01] ** 2).mean())
saida[corte:corte + len(trecho)] *= rms(b5) / rms(trecho)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s16le",
                str(A / "bloco5.wav")], input=np.clip(saida, -1, 1).tobytes(), check=True)
print(f"ok: trecho novo {len(trecho) / SR:.1f}s inserido em {corte / SR:.2f}s do bloco 5")
