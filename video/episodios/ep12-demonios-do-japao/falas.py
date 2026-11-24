"""Falas do Ep. 12 (Demônios do Japão; cópia do Ep. 11, 24/11). Comentários <!-- --> e marcas `[ ]` não são falados.
Base: Ep. 11 tiradas do ROTEIRO.md (16/11; base: o do Ep. 09).
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
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"`\[.*?\]`\s*", "", s)
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
            secoes[nome.split(":")[0] if re.search(r" — \d", nome) else nome.split(" — ")[0]] = len(falas)
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
PRON = [("Ushi no toki mairi", "Úxi no tóki mairí"), ("Hyakki Yagyō", "Riáki Iaguiô"), ("Shuten-dōji", "Xúten Dôdji"),
        ("Tamamo-no-Mae", "Tamâmo no Mái"), ("Sesshō-seki", "Sêsho-sêqui"), ("Watanabe no Tsuna", "Uatanábe no Tsúna"),
        ("Fujiwara no Morosuke", "Fudjiuára no Morôsuke"), ("Toriyama Sekien", "Toriiáma Sêkien"),
        ("Saru-ga-tsuji", "Sáru-ga-tsúdji"), ("Enryaku-ji", "Enriáku-dji"), ("Shinju-an", "Xindju-ân"),
        ("Hashihime", "Rachi-rríme"), ("Hannya", "Rânhia"), ("yōkais", "iôcais"), ("yōkai", "iôcai"), ("Raikō", "Ráicô"),
        ("tsuchigumo", "tsutchigúmo"), ("jorōgumo", "djorôgúmo"), ("ushi-oni", "úxi-ôni"), ("nure-onna", "núre-ôna"),
        ("Kubizuka", "Kubizúca"), ("Michizane", "Mitchizâne"), ("Tenjin", "Tên-djin"), ("Kifune", "Kifúne"), ("Uji", "Údji"),
        ("Modoribashi", "Modori-báxi"), ("Setsubun", "Setsubún"), ("Nō", "Nô"), ("Ōe", "Ôe"), ("Watanabe", "Uatanábe"),
        ("Sugawara", "Sugauára"), ("Minamoto", "Minamôto"), ("Oinosaka", "Oinossáka"), ("Yoshino", "Ioxíno"),
        ("Yoshitoshi", "Ioxitôxi"), ("Kuniyoshi", "Kuniôxi"), ("Hokusai", "Rokussái"), ("Sekien", "Sêkien"),
        ("rokurokubi", "rokurokúbi"), ("nurikabe", "nurikábe"), ("tsukumogami", "tsukumogâmi"), ("kamaitachi", "kamaitátchi"),
        ("satori", "satôri"), ("kimon", "kímon"), ("Kanawa", "Kanáua"), ("Gozu", "Gôzu"), ("Mezu", "Mêzu"), ("Nasu", "Nássu"),
        ("onis", "ônis"), ("oni", "ôni"), ("Izu", "Ízu"), ("Hyakki", "Riáki")]


def para_tts(t):
    t = t.replace("*", "")
    for a, b in PRON:
        t = re.sub(rf"(?<![\w-]){re.escape(a)}(?![\w-])", b, t)
    return t


if __name__ == "__main__":
    f, p, s, pa, d = ler()
    print(s); print(p); print(pa)
    for i, x in enumerate(f):
        print(i, ("[%s] " % p[i]) if i in p else "", x[:120])
