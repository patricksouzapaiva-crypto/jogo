"""Ep. 09 — amostras das vozes da Bia (22 anos, BH) e da mãe em vozes do Gemini TTS, para o usuário escolher.
Não repete as vozes do Ep. 08 (Dani = Aoede, mãe = Gacrux) para não soar igual."""
import base64, os, time, wave, requests
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent"
AQUI = os.path.dirname(os.path.abspath(__file__))
FALAS = {
 "bia1": ("Fale em português do Brasil, com sotaque mineiro leve, animada e rindo, como uma moça de 22 anos mandando "
          "um áudio no grupo da família, achando graça: ", "Gente, é tipo novela de terror, eu amei!"),
 "bia2": ("Fale em português do Brasil, com sotaque mineiro leve, baixinho e assustada, como uma moça de 22 anos "
          "mandando um áudio no celular, nervosa, tentando parecer calma: ",
          "Ela disse que aqui só se escreve em vermelho o nome de quem já morreu."),
 "bia3": ("Fale em português do Brasil, sussurrando quase sem voz, apavorada, devagar, com a respiração curta, como "
          "uma moça sozinha num quarto escuro gravando um áudio com o celular colado na boca: ",
          "Mãe... tem alguém me chamando no corredor. ... Com a sua voz."),
 "mae1": ("Fale em português do Brasil, com sotaque mineiro, como uma mãe de uns 50 anos no telefone, aflita, "
          "implorando, a voz firme mas quebrando: ", "Filha, sai desse lugar. Pelo amor de Deus. Vem pra casa."),
 "mae2": ("Fale em português do Brasil, com sotaque mineiro, como uma mãe de uns 50 anos gravando um áudio muito "
          "baixinho, cansada, com carinho, depois de meses sem notícia da filha, quase sem forças: ",
          "Filha... a mãe tá aqui."),
 # a voz falsa no corredor: a mesma voz da mãe, mas sussurrada, lenta e sem emoção (o filtro do corredor vem depois)
 "voz1": ("Fale em português do Brasil, com sotaque mineiro, sussurrando bem devagar, sem nenhuma emoção, como alguém "
          "encostado do outro lado de uma porta, chamando baixinho, com pausas longas: ", "Bia... abre. ... É a mãe."),
}
VOZES = {"bia": ["Leda", "Zephyr", "Laomedeia"], "mae": ["Sulafat", "Vindemiatrix", "Achernar"], "voz": ["Sulafat"]}
for chave, (estilo, fala) in FALAS.items():
    for voz in VOZES[chave[:3]]:
        saida = f"{AQUI}/brutas/{chave}_{voz}.wav"
        if os.path.exists(saida): continue
        corpo = {"contents": [{"parts": [{"text": estilo + fala}]}],
                 "generationConfig": {"responseModalities": ["AUDIO"],
                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}}
        for tent in range(4):
            r = requests.post(URL, headers={"x-goog-api-key": "proxy"}, json=corpo, timeout=180)
            if r.status_code == 200: break
            print(chave, voz, r.status_code, r.text[:150], flush=True); time.sleep(20)
        else: continue
        p = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
        b = base64.b64decode(p["data"]); taxa = 24000
        if "rate=" in p["mimeType"]: taxa = int(p["mimeType"].split("rate=")[1].split(";")[0])
        with wave.open(saida, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(b)
        print("ok", chave, voz, f"{len(b) / 2 / taxa:.1f}s", flush=True)
