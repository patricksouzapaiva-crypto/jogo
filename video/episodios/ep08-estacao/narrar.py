"""Narração do Ep. 08 em 3 blocos (Gemini Algenib, via painel/ferramentas/narrar_fluxo.py) + vinheta fixa.
Saída: audio/bloco{1,2,3}.wav, audio/voz_completa.wav e audio/voz_com_vinheta_limpa.wav (afftdn)."""
import re, subprocess, sys
from pathlib import Path
import falas as F

AQUI = Path(__file__).parent
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
SONS = AQUI.parents[1] / "painel" / "sons"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
fl, pers, sec, pausas, _ = F.ler()
cortes = [0, sec["PARTE 4"], sec["A HISTÓRIA"], len(fl)]
quebras = set(sec.values()) | set(pausas)
for b in range(3):
    saida = AQUI / "audio" / f"bloco{b + 1}.wav"
    if saida.exists() and "--refazer" not in sys.argv:
        continue
    txt, par = [], []
    for i in range(cortes[b], cortes[b + 1]):
        if i in quebras and par:
            txt.append(" ".join(par)); par = []
        par.append(EMOJI.sub("", F.para_tts(fl[i])).strip())
    txt.append(" ".join(par))
    tf = AQUI / "audio" / f"bloco{b + 1}.txt"; tf.write_text("\n\n".join(txt) + "\n")
    for tent in range(4):
        r = subprocess.run([sys.executable, str(FERR), str(tf), str(saida)], env={**__import__("os").environ, "VOZ": "Algenib"})
        if r.returncode == 0 and saida.exists(): break
        __import__("time").sleep(30)
lista = AQUI / "audio" / "lista.txt"
lista.write_text("".join(f"file 'bloco{b + 1}.wav'\nfile 'silencio.wav'\n" for b in range(3)) + "file 'vinheta.wav'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "1.4", str(AQUI / "audio/silencio.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SONS / "vinheta_cta_voz.wav"), "-ar", "24000", "-ac", "1", str(AQUI / "audio/vinheta.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c:a", "pcm_s16le", str(AQUI / "audio/voz_completa.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AQUI / "audio/voz_completa.wav"), "-af", "afftdn=nr=12:nf=-50",
                "-ar", "48000", str(AQUI / "audio/voz_com_vinheta_limpa.wav")], check=True)
print("ok")
