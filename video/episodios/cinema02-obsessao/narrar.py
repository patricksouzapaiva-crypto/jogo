"""Narração do O QUE É A CRIATURA? #2 — Obsessão (cópia do narrar.py do #1, 27/11) (Vigia = Algenib, gemini-3.8-flash-tts, via painel/ferramentas/narrar_fluxo.py), 16/11.
5 blocos. Para o timbre não mudar de um bloco para o outro (lição do Ep. 09), cada bloco a partir do 2º vai ao TTS com as
3 últimas frases do bloco anterior na frente; o Whisper acha onde o texto novo começa e o contexto é cortado fora.
Parágrafo novo (= respiro maior do TTS) nas seções e nas pausas marcadas no roteiro.
Saída: audio/bloco{1..5}.wav, audio/voz_completa.wav e audio/voz_com_vinheta_limpa.wav. Depois: alinhar.py.
Uso: python3 narrar.py [--refazer N ...]"""
import os, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np
import falas as F

AQUI = Path(__file__).parent; A = AQUI / "audio"; A.mkdir(exist_ok=True)
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
SONS = AQUI.parents[1] / "painel" / "sons"
SR = 24000
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
fl, sec, direc, _ = F.ler()
# 22/11 (r7): roteiro reordenado + as falas das fichas DENTRO da narração (antes eram gravações à parte, com outra voz)
CORTES = [0, sec["SUSPEITO 2 — A AMARRAÇÃO"], sec["A CIÊNCIA — EROTOMANIA"], sec["⚠️ SPOILER — O FINAL EXPLICADO ⚠️"],
          sec["O VEREDITO"], len(fl)]
QUEBRAS = set(sec.values()) | set(direc)   # parágrafo novo (respiro) a cada seção e a cada cena/peça
_modelo = None


def palavras(wav):
    global _modelo
    from faster_whisper import WhisperModel
    _modelo = _modelo or WhisperModel("small", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    seg, _ = _modelo.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    return [(norm(w.word).strip(), w.start, w.end) for s in seg for w in s.words]


def achar(ws, alvo):
    alvo = norm(alvo).split()
    for n in (3, 2):
        for i in range(1, len(ws) - n):
            if [w[0] for w in ws[i:i + n]] == alvo[:n]:
                return i
    # o Whisper escreve número por extenso como algarismo ("dois mil e vinte e um" → "2021"): acha a 1ª palavra do
    # texto seguida de um número e, logo depois, das palavras que vêm após o número no roteiro
    num = {"um", "dois", "tres", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "mil", "e", "vinte", "cem", "cento"}
    k = 1
    while k < len(alvo) and alvo[k] in num: k += 1
    resto = alvo[k:k + 1]   # só a 1ª palavra depois do número (o Whisper troca "esse" por "este")
    for i in range(1, len(ws) - 4):
        if ws[i][0] == alvo[0] and ws[i + 1][0].isdigit() and [w[0] for w in ws[i + 2:i + 2 + len(resto)]] == resto:
            return i
    # 21/11: o número no começo ("Há quatro mil anos" → "a 4 000 anos"): acha as 3 palavras seguintes e volta até o começo
    for j in range(1, 5):
        for i in range(2, len(ws) - 3):
            if [w[0] for w in ws[i:i + 3]] == alvo[j:j + 3]:
                k = i
                while k > 1 and (ws[k - 1][0].isdigit() or ws[k - 1][0] in num):
                    k -= 1
                if ws[k - 1][0][:1] == alvo[0][:1] or ws[k - 1][0] in ("a", "ha"):
                    k -= 1
                return k
    return None


def texto(i0, i1):
    out, par = [], []
    for i in range(i0, i1):
        if i in QUEBRAS and par:
            out.append(" ".join(par)); par = []
        par.append(EMOJI.sub("", F.para_tts(fl[i])).strip())
    out.append(" ".join(par))
    return "\n\n".join(out)


def tts(arq_txt, saida):
    for _ in range(4):
        r = subprocess.run([sys.executable, str(FERR), str(arq_txt), str(saida)], env={**os.environ, "VOZ": "Algenib"})
        if r.returncode == 0 and saida.exists():
            return
        __import__("time").sleep(30)
    sys.exit(f"TTS falhou: {saida.name} (cota?)")


refazer = {int(a) for a in sys.argv[1:] if a.isdigit()}
for b in range(5):
    saida = A / f"bloco{b + 1}.wav"
    if saida.exists() and (b + 1) not in refazer:
        continue
    i0, i1 = CORTES[b], CORTES[b + 1]
    if b == 0:
        (A / "bloco1.txt").write_text(texto(i0, i1) + "\n"); tts(A / "bloco1.txt", saida); continue
    ctx = " ".join(EMOJI.sub("", F.para_tts(f)).strip() for f in fl[i0 - 3:i0])
    (A / f"bloco{b + 1}.txt").write_text(ctx + "\n\n" + texto(i0, i1) + "\n")
    bruto = A / f"bloco{b + 1}_bruto.wav"
    if not bruto.exists():   # cota do TTS é curta (10/dia): o bruto já gerado é reaproveitado
        tts(A / f"bloco{b + 1}.txt", bruto)
    ws = palavras(bruto); k = achar(ws, F.para_tts(fl[i0]))
    if k is None:
        sys.exit(f"bloco {b + 1}: não achei o começo em: {' '.join(w[0] for w in ws[:50])}")
    c0 = (ws[k - 1][2] + ws[k][1]) / 2
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c0:.3f}", "-i", str(bruto), "-af", "afade=t=in:d=0.03", str(saida)], check=True)
    print(f"bloco {b + 1}: contexto cortado em {c0:.2f}s; ouvido: {' '.join(w[0] for w in ws[k:k + 10])}", flush=True)
# junta: blocos + respiro + vinheta fixa do canal; limpeza leve
lista = A / "lista.txt"
lista.write_text("".join(f"file 'bloco{b + 1}.wav'\nfile 'silencio.wav'\n" for b in range(5)) + "file 'vinheta.wav'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", "1.4", str(A / "silencio.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(SONS / "vinheta_cta_voz.wav"), "-ar", str(SR), "-ac", "1", str(A / "vinheta.wav")], check=True)
for b in range(5):   # todos no mesmo formato para o concat
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(A / f"bloco{b + 1}.wav"), "-ar", str(SR), "-ac", "1", str(A / f"_b{b + 1}.wav")], check=True)
    os.replace(A / f"_b{b + 1}.wav", A / f"bloco{b + 1}.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c:a", "pcm_s16le", str(A / "voz_completa.wav")], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(A / "voz_completa.wav"), "-af", "afftdn=nr=12:nf=-50", "-ar", "48000",
                str(A / "voz_com_vinheta_limpa.wav")], check=True)
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(A / "voz_completa.wav")], capture_output=True, text=True).stdout)
print(f"ok: narração {d / 60:.1f} min")
