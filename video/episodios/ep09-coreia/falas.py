"""Falas do Ep. 09 tiradas do ROTEIRO.md.
- Cada frase (linha lógica) das seções GANCHO…FECHO = 1 batida. Linhas quebradas no meio (sem pontuação final) são
  juntadas com a seguinte.
- Linhas de direção "*( … )*" (podem ocupar várias linhas) não são faladas; "*(pausa…)*" vira pausa antes da batida
  seguinte (PAUSAS[i] = segundos).
- "🎙bia / 🎙mae / 🎙voz" marca fala de personagem (o Vigia narra; trocar_vozes.py troca pela voz escolhida;
  "voz" = a voz falsa da mãe no corredor).
- "🎬 *( … )*" = trecho de filme (direção, não é falado; FILMES[i] = texto da direção).
- Pausas com tempo: "*(5 s: …)*" = 5 s; "*(4 batidas …)*" = 3,2 s; "*(silêncio …)*" = 2,4 s."""
import re
from pathlib import Path

AQUI = Path(__file__).parent
FILMES = {}
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
            secoes[nome.split(":")[0] if nome.startswith(("A BIA", "O RAFA")) else nome.split(" — ")[0]] = len(falas)
            continue
        if not l:
            continue
        m = re.match(r"🎙(\w+)\s+(.*)", l)
        if m:
            if buf:
                falas.append(buf); buf = ""
            personagens[len(falas)] = m.group(1); l = m.group(2)
        l = l.replace("*", "")                      # itálico do markdown não vai pra legenda
        buf = (buf + " " + l).strip() if buf else l
        if buf.endswith(FIM_FRASE):
            falas.append(buf); buf = ""
    if buf:
        falas.append(buf)
    return falas, personagens, secoes, pausas, direcoes


def para_tts(t):
    t = t.replace("*", "").replace("Yeou Nui", "Iêu Nui")
    return t


if __name__ == "__main__":
    f, p, s, pa, d = ler()
    print(s); print(p); print(pa)
    for i, x in enumerate(f):
        print(i, ("[%s] " % p[i]) if i in p else "", x[:120])
