"""Ep. 09 v3 — vozes dos personagens (Gemini TTS). Rodada 1: AMOSTRAS (uma fala de cada, 3 vozes por personagem)
para o usuário escolher. Rodada 2 (depois da escolha): todas as falas na voz escolhida.
Não repete a narração (Algenib) nem as vozes do Ep. 08 (Aoede, Gacrux). Mãe = Sulafat (já aprovada).
O TTS lê a instrução de estilo em voz alta: cortar.py tira esse pedaço (Whisper).
Uso: python3 gerar_vozes.py amostras   |   python3 gerar_vozes.py todas  (com ESCOLHA preenchida)"""
import base64, os, sys, time, wave, requests
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent"
AQUI = os.path.dirname(os.path.abspath(__file__)); os.makedirs(f"{AQUI}/brutas", exist_ok=True)
BR = "Fale em português do Brasil, com sotaque mineiro leve, "
FALAS = {
 # Rafa, 27 anos
 "rafa1": (BR + "sussurrando, apavorado, a respiração curta, como um rapaz de 27 anos gravando um áudio de dentro de um "
           "elevador escuro, com o celular colado na boca: ",
           "Mãe... eu tô no elevador. Ele tá subindo. ... E esse prédio não tem dez andares."),
 "rafa2": (BR + "exausto, a voz tremendo, quase chorando de alívio e medo, como um rapaz ligando para a mãe ao amanhecer: ",
           "Mãe. Eu achei a Lívia. ... A de verdade. Tá aqui comigo."),
 "rafa_falso1": (BR + "gritando de longe, animado, como um rapaz chamando a irmã no meio de uma mata: ",
                 "Lívia! Aqui! Vem ver isso!"),
 # Lívia, 19 anos
 "livia1": (BR + "gritando de longe, animada e rindo no fim, como uma moça de 19 anos chamando o irmão no meio de uma mata: ",
            "Rafa! Aqui! Vem ver isso!"),
 "livia2": (BR + "sonolenta, baixinho, como uma moça de 19 anos que acabou de acordar, chamando do quarto: ",
            "Oppa? ... Não consegue dormir?"),
 "livia3": (BR + "chorando baixinho, fraca, quase sem voz, como uma moça presa num quarto escuro há dias: ", "Rafa..."),
 "livia4": (BR + "sussurrando sem voz, apavorada, bem devagar: ", "Não fala nada. ... Ela tá ouvindo."),
 # a voz falsa: a mesma moça, mas calma demais, sem emoção, perto do ouvido
 "falsa1": (BR + "sussurrando muito perto, calma demais, sem nenhuma emoção, doce e errada ao mesmo tempo: ",
            "Rafa... sou eu. ... Olha pra mim."),
 "falsa2": (BR + "sussurrando muito perto, calma demais, sem emoção: ", "Oppa. ... Olha pra mim."),
 "falsa3": (BR + "falando devagar, com um sorriso na voz, calma demais: ", "Oppa. ... Você voltou."),
 # pai, uns 55 anos
 "pai1": (BR + "como um pai de uns 55 anos mandando áudio no grupo, cansado, tentando acalmar o filho: ",
          "Filho, você tá estressado. Ela tá viva, é isso que importa."),
 # mãe (Sulafat)
 "mae1": (BR + "como uma mãe de uns 50 anos mandando áudio, desesperada, chorando: ", "Rafa, pelo amor de Deus, me fala que achou ela."),
 "mae2": (BR + "como uma mãe ao telefone, confusa, calma, sem entender: ",
          "Que Lívia, filho? ... A Lívia chegou ontem. Pegou o voo sozinha. Tá aqui do meu lado."),
}
CANDIDATAS = {"rafa": ["Puck", "Iapetus", "Umbriel"], "livia": ["Zephyr", "Laomedeia", "Despina"],
              "pai": ["Charon", "Orus", "Rasalgethi"]}
AMOSTRA = {"rafa": "rafa1", "livia": "livia1", "pai": "pai1"}
ESCOLHA = {"rafa": "Umbriel", "livia": "Despina", "pai": "Orus"}   # escolhidas pelo usuário (14/11); mãe = Sulafat


def dono(chave):
    return "rafa" if chave.startswith("rafa") else "livia" if chave.startswith(("livia", "falsa")) else chave.rstrip("0123456789")


def gerar(chave, voz):
    saida = f"{AQUI}/brutas/{chave}_{voz}.wav"
    if os.path.exists(saida):
        return
    estilo, fala = FALAS[chave]
    corpo = {"contents": [{"parts": [{"text": estilo + fala}]}],
             "generationConfig": {"responseModalities": ["AUDIO"],
                                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}}
    for tent in range(4):
        r = requests.post(URL, headers={"x-goog-api-key": "proxy"}, json=corpo, timeout=180)
        if r.status_code == 200:
            break
        print(chave, voz, r.status_code, r.text[:150], flush=True); time.sleep(20)
    else:
        return
    p = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
    b = base64.b64decode(p["data"]); taxa = 24000
    if "rate=" in p["mimeType"]:
        taxa = int(p["mimeType"].split("rate=")[1].split(";")[0])
    with wave.open(saida, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(b)
    print("ok", chave, voz, f"{len(b) / 2 / taxa:.1f}s", flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["amostras"]:
        for pers, vozes in CANDIDATAS.items():
            for voz in vozes:
                gerar(AMOSTRA[pers], voz)
    else:
        vozes = {**ESCOLHA, "mae": "Sulafat"}
        for chave in FALAS:
            gerar(chave, vozes[dono(chave)])
