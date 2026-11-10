"""Traduz uma legenda .srt mantendo numeração e tempos (só o texto vai para o Gemini, em lotes; a resposta
precisa ter o mesmo número de linhas — senão o lote é refeito).
Uso: python3 traduzir_srt.py entrada.srt saida.srt <idioma: es|en>"""
import json, re, sys, time
import requests

IDIOMAS = {"es": "Spanish (Latin America)", "en": "English (US)"}
MODELO = "gemini-3.8-flash"


def ler(arq):
    blocos = re.split(r"\n\s*\n", open(arq, encoding="utf-8").read().strip())
    out = []
    for b in blocos:
        l = b.split("\n")
        out.append((l[0], l[1], " ".join(l[2:])))
    return out


def traduz(textos, idioma, contexto):
    prompt = (f"You are translating the subtitles of a Brazilian horror story video (narrated by a host called 'O Vigia', "
              f"channel 'Último Abrigo') into {IDIOMAS[idioma]}. Keep the tension, short spoken style, and the ellipses. "
              "Keep proper names as they are (Júlia, Aurélio, Dona Cida, Lucas, Giovanni Caputo, Lovecraft, Último Abrigo). "
              "Each item is one subtitle line; lines may be fragments of a sentence that continues in the next line — "
              "translate each fragment so that consecutive lines still read naturally. "
              f"Return ONLY a JSON array of exactly {len(textos)} strings, in the same order.\n\n"
              f"Previous lines for context (do not translate): {json.dumps(contexto, ensure_ascii=False)}\n\n"
              f"Lines to translate: {json.dumps(textos, ensure_ascii=False)}")
    for tentativa in range(4):
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent",
                          headers={"x-goog-api-key": "proxy"},
                          json={"contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}},
                          timeout=300)
        if r.status_code != 200:
            print("  erro", r.status_code, r.text[:200]); time.sleep(10); continue
        try:
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            lista = json.loads(txt)
            if isinstance(lista, list) and len(lista) == len(textos):
                return [str(x).strip() for x in lista]
            print(f"  lote veio com {len(lista)} linhas (esperado {len(textos)}); refazendo")
        except Exception as e:
            print("  resposta inválida:", e)
    raise SystemExit("não consegui traduzir um lote")


def main():
    ent, sai, idioma = sys.argv[1:4]
    bl = ler(ent)
    textos = [t for _, _, t in bl]
    trad = []
    for i in range(0, len(textos), 60):
        trad += traduz(textos[i:i + 60], idioma, textos[max(0, i - 4):i])
        print(f"  {idioma}: {min(i + 60, len(textos))}/{len(textos)}")
    with open(sai, "w", encoding="utf-8") as f:
        f.write("\n".join(f"{n}\n{tc}\n{t}\n" for (n, tc, _), t in zip(bl, trad)))
    print("ok:", sai)


if __name__ == "__main__":
    main()
