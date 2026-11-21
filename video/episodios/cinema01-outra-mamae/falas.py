"""Falas do O QUE É A CRIATURA? #1 (Outra Mamãe) tiradas do ROTEIRO.md v6 (21/11).
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
    corpo = s[s.index("## GANCHO"):s.index("\n---\n### Fontes")]
    falas, secoes, direcoes, som = [], {}, {}, {}
    for l in corpo.splitlines():
        l = l.strip()
        if not l:
            continue
        if l.startswith("## "):
            secoes[l[3:].strip()] = len(falas); continue
        for d in re.findall(r"`([^`]+)`", l):
            direcoes.setdefault(len(falas), []).append(d)
            if d.startswith("[CENA") and "🔊" in d:
                som.setdefault(len(falas), []).append(d)
        l = re.sub(r"`[^`]+`", "", l).strip()
        if not l:
            continue
        m = re.match(r"\*\*PISTA (\d) — (.+?)\*\*$", l)
        if m:
            falas.append(f"Pista {NUM[m.group(1)]}. {m.group(2).capitalize()}."); continue
        m = re.match(r"\*\*(\d)\. (.+?)\*\*\s*(.*)", l)
        if m:
            falas.append(f"Prova {NUM[m.group(1)]}. {m.group(2)}")
            l = m.group(3)
        l = l.replace("*", "")
        falas.extend(frases(l))
    return falas, secoes, direcoes, som


PRON = [("Rob Savage", "Róbi Sávedj"), ("James Wan", "Djêims Uân"), ("Jessica Chastain", "Djéssica Chastêin"),
        ("Incidents Around the House", "Íncidents Arráund de Ráus"), ("Josh Malerman", "Djósh Mêilerman"),
        ("changeling", "tchêindj-lin"), ("bortbyting", "bórt-bíuting"), ("Ballyvadlea", "Bálivad-lêi"),
        ("Tipperary", "Tiperéri"), ("Bridget", "Brídjet"), ("Cleary", "Clíri"), ("Boland", "Bôland"),
        ("Michael", "Máicol"), ("Denis Ganey", "Dénis Guêini"), ("fetch", "fétch"), ("doppelgänger", "dópel-guénguer"),
        ("Lamashtu", "Lamáshtu"), ("Alexandra David-Néel", "Alexandra Davíd-Neél"), ("Lucy Clifford", "Lúci Clífford"),
        ("Neil Gaiman", "Níl Gueiman"), ("Coraline", "Córalain"), ("Joseph Capgras", "Jozéf Capgrá"), ("Capgras", "Capgrá"),
        ("Russ", "Râss"), ("Kelvin", "Kélvin"), ("Frank", "Frénk"), ("Ruth", "Rúti"), ("Lois", "Lôis")]


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
