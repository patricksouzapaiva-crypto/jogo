"""Monta en/voz_completa_en.wav garantindo que TODAS as falas foram narradas.
O TTS 3.1 corta pedidos longos (~2 min de áudio, finishReason SAFETY): aproveita o trecho completo de cada
pedido, corta no fim da última frase inteira e pede o resto de novo, em pedaços menores, até cobrir tudo.
REGRA: o inglês não usa o modelo principal (gemini-3.8); usa o 3.1 (e o 2.5 se o 3.1 ficar sem cota)."""
import hashlib, subprocess, sys
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / "painel")); sys.path.insert(0, str(AQUI))
import gerar  # noqa: E402
gerar.IDIOMA["whisper"] = "en"
from gerar import CACHE, tokens, norm, transcrever, narrar  # noqa: E402
from traducao_en import EN  # noqa: E402

SR = 48000
MODELOS = ["gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]
VOZ = "Algenib"
RAFAEL = {"modelo": "gemini-2.5-flash-preview-tts", "nome": "Puck",
          "estilo": "Whisper urgently and fearfully, out of breath, like a frightened man leaving a voice message "
                    "at 3 AM, trying not to be heard"}


def ler(w, cortar_silencio=True):
    af = ["-af", "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.12,areverse,"
                 "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.25,areverse"] if cortar_silencio else []
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), *af, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def tts(idx):
    texto = "\n".join(EN[i][0] for i in idx)
    for m in MODELOS:
        w = CACHE / ("en_" + hashlib.sha1(f"{m}|{VOZ}|{texto}".encode()).hexdigest()[:16] + ".wav")
        if w.exists():
            return w
    for m in MODELOS:
        w = CACHE / ("en_" + hashlib.sha1(f"{m}|{VOZ}|{texto}".encode()).hexdigest()[:16] + ".wav")
        t = CACHE / "en_bloco.txt"; t.write_text(texto, encoding="utf-8")
        r = subprocess.run([sys.executable, str(AQUI / "tts_stream.py"), m, VOZ, str(t), str(w)],
                           capture_output=True, text=True)
        print("   ", m, (r.stdout + r.stderr).strip().splitlines()[-1][:120])
        if w.exists():
            return w
    raise SystemExit("sem cota nos modelos de inglês hoje")


def cobertura(w, idx):
    """Quais batidas de idx foram faladas por inteiro, e o fim (s) da última delas."""
    ouv = transcrever(w, "")
    on = [norm(x[0]) for x in ouv]
    feitas, pos, fim = [], 0, 0.0
    for i in idx:
        ult = norm(tokens(EN[i][0])[-1])
        try:
            j = on.index(ult, pos)
        except ValueError:
            break
        feitas.append(i); pos = j + 1; fim = ouv[j][2]
    return feitas, fim


def narrar_faixa(idx, maxc=1100):
    """Devolve lista de arrays de áudio cobrindo todas as batidas de idx, em ordem."""
    saida, resto = [], list(idx)
    while resto:
        bloco, tot = [], 0
        for i in resto:
            if bloco and tot + len(EN[i][0]) > maxc:
                break
            bloco.append(i); tot += len(EN[i][0])
        w = tts(bloco)
        feitas, fim = cobertura(w, bloco)
        if not feitas:  # nem a primeira frase saiu inteira: pede só ela
            w = tts(bloco[:1]); feitas, fim = cobertura(w, bloco[:1])
            if not feitas:
                raise SystemExit(f"a batida {bloco[0]} não sai no TTS")
        a = ler(w, cortar_silencio=False)
        a = a[: int((fim + (0.35 if len(feitas) < len(bloco) else 0.6)) * SR)]
        a = ler_array(a)
        print(f"  batidas {feitas[0]}–{feitas[-1]} ok ({len(a) / SR:.1f} s)")
        saida.append(a)
        resto = resto[len(feitas):]
    return saida


def ler_array(a):
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                          "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.12,areverse,"
                          "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.25,areverse",
                          "-f", "f32le", "-"], input=a.tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, np.float32)


def sil(s):
    return np.zeros(int(s * SR), np.float32)


if __name__ == "__main__":
    import narrar_en_blocos as nb
    raf = {i: ler(narrar(EN[i][0].strip('"'), RAFAEL, CACHE)) for i in (0, 1, 2)}
    partes = []
    for i in (0, 1, 2):
        partes += [raf[i], sil(1.1)]
    partes.append(sil(0.6))
    for faixa in (range(3, 96), range(97, 133)):
        # aproveita os blocos grandes já gerados e completa o que faltou
        for bl in [b for b in nb.TODOS if b[0] in faixa]:
            w = tts(bl)
            feitas, fim = cobertura(w, bl)
            a = ler_array(ler(w, cortar_silencio=False)[: int((fim + 0.35) * SR)])
            print(f"bloco {bl[0]}–{bl[-1]}: aproveitado até {feitas[-1]} ({len(a) / SR:.1f} s)")
            partes += [a, sil(0.75)]
            falta = bl[len(feitas):]
            for x in narrar_faixa(falta):
                partes += [x, sil(0.75)]
        if faixa.start == 3:
            partes += [sil(0.4), raf[1], sil(0.6), raf[2], sil(1.2)]
    voz = np.concatenate(partes)
    dest = AQUI / "voz_completa_en.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-af", "afftdn=nr=12:nf=-50:tn=1,highpass=f=70", str(dest)], input=voz.tobytes(), check=True)
    print("pronto:", dest, f"{len(voz) / SR:.1f} s")
