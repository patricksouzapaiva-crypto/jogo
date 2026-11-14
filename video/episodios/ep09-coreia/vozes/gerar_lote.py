"""15/11 v4: o "Oppa" emendado (Ôppa aprovado + resto de outra tomada) soava como erro de execução ("nem parece fazer
parte do vídeo"). Agora cada fala sai INTEIRA, de uma vez, e TODAS as falas da Lívia/voz falsa vêm na MESMA chamada
(mesma voz, mesmo jeito de dizer "Ôppa" em todas). Sem "..." no meio (o TTS fazia uma pausa morta depois do Ôppa).
3 tomadas do lote; cortar_lote.py separa as falas pelo Whisper.
Uso: python3 gerar_lote.py [n_tomadas]   → brutas/lote_livia_t{1..n}.wav"""
import base64, os, sys, time, wave, requests
MODELO = os.environ.get("MODELO", "gemini-3.8-flash-tts")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent"
AQUI = os.path.dirname(os.path.abspath(__file__))
LIVIA = [
    ("livia1", "Rafa! Aqui! Vem ver isso!"),
    ("livia_oppa", "Ôppa."),
    ("raposa1", "Ôppa. Vocês voltaram."),
    ("livia2", "Ôppa? Não consegue dormir?"),
    ("falsa1", "Rafa, sou eu. Olha pra mim."),
    ("falsa2", "Ôppa, olha pra mim."),
    ("livia3", "Rafa."),
    ("livia4", "Não fala nada. Ela tá ouvindo."),
    ("falsa3", "Ôppa. Você voltou."),
]
INSTR = ("Leia em português do Brasil, com sotaque mineiro leve, na voz de uma moça de dezenove anos, baixinho, perto, "
         "calma, natural, como se falasse com o irmão mais velho. A palavra Ôppa se pronuncia sempre igual: Ô-pa, com o "
         "o fechado e o p forte. Faça uma pausa de dois segundos entre cada fala.\n\n")


def gerar(saida, voz="Despina"):
    texto = INSTR + "\n\n".join(f for _, f in LIVIA)
    corpo = {"contents": [{"parts": [{"text": texto}]}],
             "generationConfig": {"responseModalities": ["AUDIO"],
                                  "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voz}}}}}
    for t in range(4):
        r = requests.post(URL, headers={"x-goog-api-key": "proxy"}, json=corpo, timeout=240)
        if r.status_code == 200:
            break
        print(r.status_code, r.text[:200], flush=True); time.sleep(20)
    else:
        return False
    p = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
    b = base64.b64decode(p["data"]); taxa = int(p["mimeType"].split("rate=")[1].split(";")[0]) if "rate=" in p["mimeType"] else 24000
    with wave.open(saida, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(b)
    print("ok", saida, f"{len(b) / 2 / taxa:.1f}s", flush=True)
    return True


if __name__ == "__main__":
    n = int(sys.argv[1]) if sys.argv[1:] else 3
    for k in range(1, n + 1):
        s = f"{AQUI}/brutas/lote_livia_t{k}.wav"
        if not os.path.exists(s):
            gerar(s)
