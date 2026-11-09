"""Narração longa pelo Gemini em fluxo (streamGenerateContent): o áudio chega aos pedaços e a conexão não
cai por inatividade (a chamada normal com ~14 min de texto dá 502 depois de ~30 s).
Uso: python3 narrar_fluxo.py texto.txt saida.wav   — NÃO TESTADO ATÉ O FIM ainda (cota acabou em 09/11)."""
import json, sys, time, base64, io, wave, requests, numpy as np
texto = open(sys.argv[1]).read(); saida = sys.argv[2]
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:streamGenerateContent?alt=sse"
corpo = {"contents": [{"parts": [{"text": texto}]}],
         "generationConfig": {"responseModalities": ["AUDIO"],
                              "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Algenib"}}}}}
t0 = time.time()
r = requests.post(url, headers={"x-goog-api-key": "proxy"}, json=corpo, stream=True, timeout=900)
print("status", r.status_code, flush=True)
if r.status_code != 200:
    print(r.text[:800]); sys.exit(1)
pcm, taxa, n = [], 24000, 0
for linha in r.iter_lines():
    if not linha.startswith(b"data: "): continue
    d = json.loads(linha[6:])
    for p in d.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" not in p: continue
        b = base64.b64decode(p["inlineData"]["data"]); mt = p["inlineData"]["mimeType"]
        if "wav" in mt:
            w = wave.open(io.BytesIO(b)); taxa = w.getframerate(); b = w.readframes(w.getnframes())
        elif "rate=" in mt:
            taxa = int(mt.split("rate=")[1].split(";")[0])
        pcm.append(b); n += 1
        if n % 10 == 1: print(f"  pedaço {n} em {time.time()-t0:.0f}s", flush=True)
    fr = d.get("candidates", [{}])[0].get("finishReason")
    if fr and fr != "STOP": print("fim:", fr)
a = b"".join(pcm)
with wave.open(saida, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(a)
print(f"ok: {len(a)/2/taxa:.1f}s de áudio em {time.time()-t0:.0f}s, {n} pedaços")
