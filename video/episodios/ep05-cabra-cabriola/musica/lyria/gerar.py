"""Gera música com o Lyria (API do Gemini, mesma chave/proxy da narração). Uso: python3 gerar.py saida_base "prompt" [modelo]
Grava saida_base.<ext> com o áudio devolvido (e imprime o texto, se vier)."""
import base64, json, sys, urllib.request, urllib.error
saida, prompt = sys.argv[1], sys.argv[2]
modelo = sys.argv[3] if len(sys.argv) > 3 else "lyria-3.5"
corpo = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
         "generationConfig": {"responseModalities": ["AUDIO", "TEXT"]}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                             data=json.dumps(corpo).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": "dummy"})
try:
    r = json.load(urllib.request.urlopen(req, timeout=600))
except urllib.error.HTTPError as e:
    print("ERRO", e.code, e.read().decode()[:600]); sys.exit(1)
n = 0
for c in r.get("candidates", []):
    for p in c.get("content", {}).get("parts", []):
        if "inlineData" in p:
            mime = p["inlineData"].get("mimeType", "audio/wav"); ext = mime.split("/")[-1].split(";")[0].replace("mpeg", "mp3").replace("x-wav", "wav")
            arq = f"{saida}{'' if n == 0 else '_' + str(n)}.{ext}"
            open(arq, "wb").write(base64.b64decode(p["inlineData"]["data"])); print("ok:", arq, mime); n += 1
        elif "text" in p:
            print("texto:", p["text"][:300])
if not n:
    print("sem áudio:", json.dumps(r)[:600])
