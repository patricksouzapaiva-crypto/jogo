"""TTS do Gemini em streaming (evita o 502 de pedidos longos). Uso: tts_stream.py modelo voz arquivo_texto saida.wav [estilo]"""
import base64, json, subprocess, sys, requests
modelo, voz, arq, saida = sys.argv[1:5]
estilo = sys.argv[5] if len(sys.argv) > 5 else ""
texto = open(arq, encoding="utf-8").read()
prompt = f"{estilo}:\n\n{texto}" if estilo else texto
r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:streamGenerateContent?alt=sse",
                  headers={"x-goog-api-key": "proxy"}, stream=True, timeout=900,
                  json={"contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseModalities": ["AUDIO"],
                                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}})
if r.status_code != 200:
    print(r.status_code, r.text[:400]); sys.exit(1)
pcm, taxa = bytearray(), 24000
for linha in r.iter_lines():
    if not linha.startswith(b"data:"):
        continue
    d = json.loads(linha[5:])
    for c in d.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "inlineData" in p:
                pcm += base64.b64decode(p["inlineData"]["data"])
                mt = p["inlineData"]["mimeType"]
                if "rate=" in mt: taxa = int(mt.split("rate=")[1].split(";")[0])
        if c.get("finishReason") not in (None, "STOP"): print("finish:", c.get("finishReason"))
if not pcm:
    print("sem áudio"); sys.exit(1)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(taxa), "-ac", "1", "-i", "-", "-ar", "48000", saida],
               input=bytes(pcm), check=True)
print("ok", saida, round(len(pcm) / 2 / taxa, 1), "s")
