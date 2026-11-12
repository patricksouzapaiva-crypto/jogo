"""Gera as vozes de personagem do Ep. 08 (Dani e mãe) em várias vozes do Gemini TTS, para escolha."""
import json, sys, base64, io, wave, requests, os, time
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent"
AQUI = os.path.dirname(os.path.abspath(__file__))
FALAS = {
 "dani1": ("Fale em português do Brasil, sussurrando bem baixinho, com medo, rápido e tenso, como uma moça de 26 anos "
           "escondida gravando um áudio no celular dentro de um trem vazio, tentando não ser ouvida: ",
           "Gente... esse trem não para faz vinte minutos. E lá fora... não tem luz nenhuma. Nenhuma."),
 "dani2": ("Fale em português do Brasil, sussurrando quase sem voz, apavorada, devagar, com pausas, como uma moça "
           "sozinha numa plataforma no escuro gravando um áudio no celular bem perto da boca: ",
           "Tem um tambor tocando. Longe. ... E um sino. ... Vocês tão ouvindo?"),
 "mae":   ("Fale em português do Brasil como uma mãe brasileira de uns 55 anos, simples, falando para a câmera do "
           "celular num quintal, com a voz quebrando de choro contido, devagar, sem teatralidade: ",
           "A gente só quer a nossa filha de volta. ... Se alguém souber de alguma coisa... compartilha. ... E reza com a gente."),
}
VOZES = {"dani1": ["Leda", "Aoede", "Despina"], "dani2": ["Leda", "Aoede", "Despina"],
         "mae": ["Gacrux", "Sulafat", "Vindemiatrix"]}
for chave, (estilo, fala) in FALAS.items():
    for voz in VOZES[chave]:
        saida = f"{AQUI}/brutas/{chave}_{voz}.wav"
        if os.path.exists(saida): continue
        corpo = {"contents": [{"parts": [{"text": estilo + fala}]}],
                 "generationConfig": {"responseModalities": ["AUDIO"],
                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}}
        for tent in range(3):
            r = requests.post(URL, headers={"x-goog-api-key": "proxy"}, json=corpo, timeout=180)
            if r.status_code == 200: break
            print(chave, voz, r.status_code, r.text[:200]); time.sleep(5)
        else: continue
        p = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
        b = base64.b64decode(p["data"]); taxa = 24000
        if "rate=" in p["mimeType"]: taxa = int(p["mimeType"].split("rate=")[1].split(";")[0])
        with wave.open(saida, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(b)
        print("ok", chave, voz, f"{len(b)/2/taxa:.1f}s", flush=True)
