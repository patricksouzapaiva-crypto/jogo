"""Rascunho PARCIAL (teste do motor com a narração que já existe): os N primeiros blocos da narração + as falas que eles
cobrem. Monta roteiro_parcial.json a partir do roteiro.json e renderiza previas/ep10_parcial.mp4 (--rascunho).
Uso: python3 rascunho_parcial.py [blocos=2]"""
import json, subprocess, sys
from pathlib import Path
import falas as F
AQUI = Path(__file__).parent; A = AQUI / "audio"
nb = int(sys.argv[1]) if len(sys.argv) > 1 else 2
fl, _, sec, _, _ = F.ler()
CORTES = [0, sec["CAPÍTULO 2"], sec["CAPÍTULO 4"], sec["MATEUS — 2"], sec["FECHO"], len(fl)]
lista = A / "lista_parcial.txt"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "1.4", str(A / "silencio_p.wav")], check=True)
lista.write_text("".join(f"file 'bloco{b + 1}.wav'\nfile 'silencio_p.wav'\n" for b in range(nb)))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-af", "afftdn=nr=12:nf=-50", "-ar", "48000",
                str(A / "voz_parcial.wav")], check=True)
r = json.load(open(AQUI / "roteiro.json"))
r["batidas"] = r["batidas"][:CORTES[nb]]
r["voz_arquivo"] = "audio/voz_parcial.wav"
r.pop("cta", None)
(AQUI / "roteiro_parcial.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
subprocess.run([sys.executable, str(AQUI.parents[1] / "painel" / "gerar.py"), "roteiro_parcial.json", "previas/ep10_parcial.mp4", "--rascunho"],
               cwd=AQUI, check=True)
