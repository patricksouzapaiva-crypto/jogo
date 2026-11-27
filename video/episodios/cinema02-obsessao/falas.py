"""Falas do O QUE É A CRIATURA? #2 (Obsessão) tiradas do ROTEIRO.md v4 (27/11; cópia do falas.py do #1).
27/11: também ignora comentários <!-- -->, os títulos de ato "# …" e lê as provas no formato "1. **…:** …".
Formato novo (não é o do Ep. 11):
- Seções "## …" do GANCHO ao FECHO; o "---" antes das Fontes encerra.
- Linhas entre crases (`[CENA …]`, `[REAL …]`, `[IA …]`, `[PEÇA …]`, `[VIGIA]`, `FICHA: …`) são direção: não são faladas.
  Ficam em DIRECOES[i] = lista de direções que vêm ANTES da fala i (várias numa linha = várias direções).
- `[CENA …🔊…]` = trecho com SOM ORIGINAL do filme: o Vigia se cala e o filme fala (a montagem abre o buraco).
- Cada FRASE vira uma batida (linhas com várias frases são quebradas), para a legenda e a troca de cena andarem juntas.
- "**PISTA 1 — ELA PEDE PERMISSÃO**" é falada como "Pista um. Ela pede permissão."
- "**1. Ela pede permissão.** …" (o porquê do veredito) é falada como "Prova um. Ela pede permissão. …"."""
import re
from pathlib import Path

AQUI = Path(__file__).parent
VINHETA = ("Se você ficou até aqui… então já é um dos meus. Inscreva-se no Último Abrigo e ative o sininho, "
           "pra não perder o próximo caso. Eu vou estar aqui. Esperando.")
NUM = {"1": "um", "2": "dois", "3": "três", "4": "quatro", "5": "cinco", "6": "seis", "7": "sete", "8": "oito", "9": "nove"}
# quebra de frase: pontuação final + espaço + começo de frase nova (maiúscula, aspas ou travessão)
QUEBRA = re.compile(r'(?<=[.?!…])(["”]?)\s+(?=["“A-ZÀÁÉÍÓÚÂÊÔÃÕÇ])')


def frases(l):
    partes, ini = [], 0
    for m in QUEBRA.finditer(l):
        partes.append(l[ini:m.start()] + m.group(1)); ini = m.end()
    partes.append(l[ini:])
    # aspas abertas numa frase e fechadas na outra: junta (a citação fica inteira na legenda)
    out = []
    for p in (x.strip() for x in partes if x.strip()):
        if out and out[-1].count('"') % 2 == 1:
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def ler():
    s = (AQUI / "ROTEIRO.md").read_text(encoding="utf-8")
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    corpo = s[s.index("## GANCHO"):s.index("\n---\n### Fontes")]
    falas, secoes, direcoes, som = [], {}, {}, {}
    for l in corpo.splitlines():
        l = l.strip()
        if not l:
            continue
        if l.startswith("## "):
            secoes[l[3:].strip()] = len(falas); continue
        if l.startswith("# ") or l == "---":
            continue
        for d in re.findall(r"`([^`]+)`", l):
            direcoes.setdefault(len(falas), []).append(d)
            if d.startswith("[CENA") and "🔊" in d:
                som.setdefault(len(falas), []).append(d)
        l = re.sub(r"`[^`]+`", "", l).strip()
        if not l:
            continue
        m = re.match(r"\*\*PISTA (\d) — (.+?)\*\*$", l)
        if m:
            tit = m.group(2).replace('"', "").lower(); tit = tit[0].upper() + tit[1:]; tit = re.sub(r"\bnikki\b", "Nikki", tit).replace('"', "")
            falas.append(f"Pista {NUM[m.group(1)]}. {tit}."); continue
        m = re.match(r"\*\*(\d)\. (.+?)\*\*\s*(.*)", l) or re.match(r"(\d)\. \*\*(.+?):?\*\*:?\s*(.*)", l)
        if m:
            falas.append(f"Prova {NUM[m.group(1)]}. {m.group(2)}")
            l = m.group(3)
        l = l.replace("*", "")
        falas.extend(frases(l))
    return falas, secoes, direcoes, som


PRON = [("Nikki Freeman", "Níqui Frímen"), ("Nikki", "Níqui"), ("Bear", "Bér"), ("Sarah", "Sára"), ("Ian", "Íen"),
        ("agogé", "agoguê"), ("katadesmos", "katadésmos"), ("defixio", "defíquisio"), ("dybbuk", "dibúk"),
        ("Dibuk", "Dibúk"), ("Ansky", "Ánski"), ("Volínia", "Volínia"), ("Podólia", "Podólia"), ("Khonen", "Rônen"),
        ("Leah", "Léa"), ("jinn", "djín"), ("W. W. Jacobs", "dáblio dáblio Djêicobs"), ("Harper's", "Rárpers"),
        ("Gaëtan Gatian de Clérambault", "Gaetân Gatiân de Clerambô"), ("Clérambault", "Clerambô"),
        ("Léa-Anna", "Léa-Ana"), ("George Quinto", "Djórdj Quinto"), ("Mary Blandy", "Méri Blândi"),
        ("Francis Blandy", "Frâncis Blândi"), ("Blandy", "Blândi"), ("William Cranstoun", "Uíliam Crânstun"),
        ("Cranstoun", "Crânstun"), ("Henley-on-Thames", "Rênli on Têims"), ("Tristão e Isolda", "Tristão e Isolda"),
        ("Sarapammon", "Sarapâmon"), ("Ptolemais", "Ptolemaís"), ("Tavistock", "Távistok"), ("Cornualha", "Cornualha"),
        ("British Library", "Brítish Láibrari")]


def para_tts(t):
    t = t.replace("*", "")
    for a, b in PRON:
        t = re.sub(rf"\b{re.escape(a)}\b", b, t)
    return t


if __name__ == "__main__":
    f, s, d, so = ler()
    print(s)
    for i, x in enumerate(f):
        for dd in d.get(i, []):
            print("     ", ("🔊 " if dd in so.get(i, []) else "") + dd[:90])
        print(f"{i:3d}", x)
    print(len(f), "falas;", sum(len(x.split()) for x in f), "palavras")
