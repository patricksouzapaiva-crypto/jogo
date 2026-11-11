"""Alinha a narração (audio/voz_com_vinheta_limpa.wav) com as falas → audio/alinhamento.json + relatório."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens, transcrever, alinhar, ajustar_inicios, norm  # noqa: E402
import falas as F

AQUI = Path(__file__).parent
fl, _, _ = F.ler(); fl = fl + [F.VINHETA]
wav = AQUI / "audio" / (sys.argv[1] if len(sys.argv) > 1 else "voz_com_vinheta_limpa.wav")
pal = [w for f in fl for w in tokens(f)]
ouv = transcrever(wav, "")
json.dump(ouv, open(AQUI / "audio" / "ouvidas.json", "w"))
tempos, casadas = alinhar(pal, ouv)
tempos = ajustar_inicios(wav, tempos)
json.dump(tempos, open(AQUI / "audio" / "alinhamento.json", "w"))
print(f"{casadas:.0%} reconhecidas; {len(pal)} palavras; fim {tempos[-1][1]:.1f}s")
k = 0
for i, f in enumerate(fl):
    n = len(tokens(f)); t0, t1 = tempos[k][0], tempos[k + n - 1][1]
    print(f"{i:3d} {t0:7.2f} {t1:7.2f} {(t1 - t0) / max(n, 1):.2f}s/pal  {f[:70]}")
    k += n
