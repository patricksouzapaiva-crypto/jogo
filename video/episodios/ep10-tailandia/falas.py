"""Falas do Ep. 10 (Tailândia) tiradas do ROTEIRO.md (16/11; base: o do Ep. 09).
- No Ep. 10 a fala de personagem traz a direção NA MESMA LINHA: 🎙mateus *(23 anos, voz animada…)* "fala" —
  a direção sai (DIRECOES_PERS[i]) e só a fala entre aspas fica.
- Cada frase (linha lógica) das seções GANCHO…FECHO = 1 batida. Linhas quebradas no meio (sem pontuação final) são
  juntadas com a seguinte.
- Linhas de direção "*( … )*" (podem ocupar várias linhas) não são faladas; "*(pausa…)*" vira pausa antes da batida
  seguinte (PAUSAS[i] = segundos).
- "🎙mateus / 🎙camila" marca fala de personagem (o Vigia narra; trocar_vozes.py troca pela voz escolhida).
- "🎬 *( … )*" = trecho de filme (direção, não é falado; FILMES[i] = texto da direção).
- Pausas com tempo: "*(5 s: …)*" = 5 s; "*(4 batidas …)*" = 3,2 s; "*(silêncio …)*" = 2,4 s."""
import re
from pathlib import Path

AQUI = Path(__file__).parent
FILMES = {}
DIRECOES_PERS = {}
VINHETA = ("Se você ficou até aqui… então já é um dos meus. Inscreva-se no Último Abrigo e ative o sininho, "
           "pra não perder o próximo caso. Eu vou estar aqui. Esperando.")
FIM_FRASE = ('.', '?', '!', '…', ':', '"', '”', ')')


def ler():
    s = (AQUI / "ROTEIRO.md").read_text(encoding="utf-8")
    corpo = s[s.index("## GANCHO"):s.index("*(vinheta do Vigia)*")]
    falas, personagens, secoes, pausas, direcoes = [], {}, {}, {}, {}
    global FILMES
    FILMES = {}
    buf, em_direcao, dir_buf = "", False, ""
    for l in corpo.splitlines():
        l = l.strip()
        filme = l.startswith("🎬")
        if filme:
            l = l[1:].strip()
        if em_direcao:
            dir_buf += " " + l
            if l.endswith(")*"):
                em_direcao = False; direcoes[len(falas)] = dir_buf.strip()
            continue
        if l.startswith("*("):
            if buf:
                falas.append(buf); buf = ""
            if filme:
                FILMES.setdefault(len(falas), []).append(l)
            if l.endswith(")*"):
                m = re.match(r"\*\((\d+) s:", l)
                if m:
                    pausas[len(falas)] = float(m.group(1))
                elif l.startswith("*(4 batidas"):
                    pausas[len(falas)] = 3.2
                elif l.startswith("*(silêncio"):
                    pausas[len(falas)] = 2.4
                elif l.startswith("*(pausa"):
                    pausas[len(falas)] = 1.6
                direcoes[len(falas)] = l
            else:
                em_direcao, dir_buf = True, l
            continue
        if l.startswith("## "):
            if buf:
                falas.append(buf); buf = ""
            nome = l[3:].split(" (")[0]
            secoes[nome.split(":")[0] if nome.startswith("MATEUS") else nome.split(" — ")[0]] = len(falas)
            continue
        if not l:
            continue
        m = re.match(r"🎙(\w+)\s+(.*)", l)
        if m:
            if buf:
                falas.append(buf); buf = ""
            personagens[len(falas)] = m.group(1); l = m.group(2)
            d = re.match(r"\*\((.*?)\)\*\s*(.*)", l)
            if d:
                DIRECOES_PERS[len(falas)] = d.group(1); l = d.group(2)
        l = l.replace("*", "")                      # itálico do markdown não vai pra legenda
        buf = (buf + " " + l).strip() if buf else l
        if buf.endswith(FIM_FRASE):
            falas.append(buf); buf = ""
    if buf:
        falas.append(buf)
    return falas, personagens, secoes, pausas, direcoes


# pronúncia (a lista do fim do ROTEIRO.md): só no texto que vai para o TTS; a legenda mantém a grafia certa
PRON = [("Satsana Phi", "Satsanã Pí"), ("San Phra Phum", "Sãn Prá Púm"), ("Phi Tai Hong", "Pí Tai Rông"), ("Phi Pop", "Pí Póp"),
        ("Phi Am", "Pí Ãm"), ("Rang Song", "Rãng Sông"), ("Saiyasat", "Saiassát"), ("Pha Yant", "Pá Iãnt"), ("Sai Sin", "Sai Sín"),
        ("Nam Man Phrai", "Nãm Mãm Prai"), ("Mo Tham", "Mô Tâm"), ("Banjong Pisanthanakun", "Bandjông Pissãntanacún"),
        ("Na Hong-jin", "Ná Rông-djín"), ("Mae Nak Phra Khanong", "Mé Nác Prá Canông"), ("Krasue", "Crassú"), ("Khom", "Côm"),
        ("Isan", "Issân"), ("Loei", "Lôi"), ("Pret", "Prêt"), ("Phi", "Pí"), ("Niran", "Nirân")]


def para_tts(t):
    t = t.replace("*", "")
    for a, b in PRON:
        t = re.sub(rf"\b{re.escape(a)}\b", b, t)
    return t


if __name__ == "__main__":
    f, p, s, pa, d = ler()
    print(s); print(p); print(pa)
    for i, x in enumerate(f):
        print(i, ("[%s] " % p[i]) if i in p else "", x[:120])
