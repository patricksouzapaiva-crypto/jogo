"""Vozes do Ep. 11 (16/11): os áudios do Lucas (falas 62 e 72), no Gemini TTS. Base: o gerar_vozes.py do Ep. 10.
Cada fala sai INTEIRA numa chamada só (lição do Ep. 09: fala emendada soa como erro), com a direção de atuação do roteiro
na instrução. Amostra de vozes: python3 gerar_vozes.py --amostra  (a 1ª fala do Mateus e a da Camila em várias vozes).
Uso: python3 gerar_vozes.py [voz_mateus] [voz_camila]  → brutas/f<id>_<pers>_<voz>.wav (1 tomada: a cota é 10/dia)
e limpas_escolhidas/f<id>.wav (16/11: vozes escolhidas pelo usuário: Mateus = Iapetus, Camila = Aoede).
O TTS às vezes LÊ a instrução em voz alta: a direção vai no formato curto "Diga …: <fala>" e, de qualquer jeito, o Whisper
acha onde a fala começa (última ocorrência das 3 primeiras palavras) e o que vem antes é cortado."""
import base64, os, subprocess, sys, time, wave
import numpy as np
from pathlib import Path
import requests

AQUI = Path(__file__).parent; B = AQUI / "brutas"; B.mkdir(exist_ok=True); L = AQUI / "limpas_escolhidas"; L.mkdir(exist_ok=True)
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent"
sys.path.insert(0, str(AQUI.parent)); import falas as F   # noqa: E402
fl, pers, *_ = F.ler()
BASE = "Leia em português do Brasil, sotaque paulista, como um áudio de WhatsApp gravado no celular, natural e sem teatro. "
JEITO = {   # fala do roteiro → como dizer (a direção do roteiro, em instrução)
    62: "Rapaz de 26 anos, aliviado e ainda tremendo de frio, dentro de um quarto de madeira, falando baixo e rápido para um amigo, a voz um pouco trêmula.",
    72: "Rapaz de 26 anos, sussurro desesperado escondido atrás de um celeiro na neve, a respiração falhando de pavor e de frio, a frase se quebrando no fim.",
}


def gerar(texto, voz, saida):
    corpo = {"contents": [{"parts": [{"text": texto}]}],
             "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}}
    for k in range(5):
        r = requests.post(URL, headers={"x-goog-api-key": "proxy"}, json=corpo, timeout=300)
        if r.status_code == 200:
            p = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            with wave.open(str(saida), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(base64.b64decode(p["data"]))
            print("ok", saida.name, flush=True); return
        print(r.status_code, r.text[:160], flush=True); time.sleep(20 * (k + 1))


fala = lambda i: fl[i].strip('"“”')


def cortar(bruto, texto, saida):
    """corta o que vem antes da fala (instrução lida em voz alta), pelo Whisper"""
    from faster_whisper import WhisperModel
    import unicodedata, re
    nz = lambda t: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()).strip()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(bruto), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    seg, _ = WhisperModel("small", compute_type="int8").transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    ws = [(nz(w.word), w.start) for s_ in seg for w in s_.words]
    alvo = nz(texto).split()
    c0 = 0.0
    # a instrução termina em "Diga:" — a fala começa na palavra seguinte; sem o "diga", a 1ª ocorrência do começo da fala
    # depois da instrução (a ÚLTIMA ocorrência falhava quando a fala repete o próprio começo: "eu não posso sair…")
    dg = [k for k, w in enumerate(ws) if w[0] == "diga"]
    if dg and dg[-1] + 1 < len(ws):
        c0 = max(0.0, ws[dg[-1] + 1][1] - 0.12)
    else:
        ini = next((k for k, w in enumerate(ws) if w[0] in ("rapaz", "moca", "moça")), 0)
        for n in (3, 2, 1):
            achou = [k for k in range(ini, len(ws) - n + 1) if [w[0] for w in ws[k:k + n]] == alvo[:n]]
            if achou:
                k = achou[0]; c0 = max(0.0, ws[k][1] - 0.12) if k > 0 else 0.0; break
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c0:.3f}", "-i", str(bruto), "-af", "afade=t=in:d=0.02", str(saida)], check=True)
    print(f"  {saida.name}: cortado em {c0:.2f}s; ouvido: {' '.join(w[0] for w in ws)[:140]}", flush=True)


if "--amostra" in sys.argv:   # a amostra já é a fala 62 completa no formato final: a escolhida vira a tomada definitiva
    for v in ["Puck", "Achird", "Fenrir"]:
        arq = B / f"f62_lucas_{v}.wav"
        if not arq.exists(): gerar(f"{BASE}{JEITO[62]} Diga: {fala(62)}", v, arq)
        cortar(arq, fala(62), AQUI / "amostras" / f"lucas_{v}.wav")
    sys.exit()
vm = vc = sys.argv[1] if len(sys.argv) > 1 else "Puck"
for i, j in JEITO.items():
    voz = vc if pers[i] == "camila" else vm
    arq = B / f"f{i}_{pers[i]}_{voz}.wav"
    if not arq.exists():
        gerar(f"{BASE}{j} Diga: {fala(i)}", voz, arq)
    if arq.exists():
        cortar(arq, fala(i), L / f"f{i}.wav")
    else:
        sys.exit(f"sem a fala {i} (cota?)")
