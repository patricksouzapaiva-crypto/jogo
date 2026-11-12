"""Falas do Ep. 07 tiradas do ROTEIRO.md (cada linha de texto das seções = 1 batida). 🎙 marca fala do Caio."""
from pathlib import Path

AQUI = Path(__file__).parent
VINHETA = ("Se você ficou até aqui… então já é um dos meus. Inscreva-se no Último Abrigo e ative o sininho, "
           "pra não perder o próximo caso. Eu vou estar aqui. Esperando.")


def ler():
    s = (AQUI / "ROTEIRO.md").read_text(encoding="utf-8")
    corpo = s[s.index("## GANCHO"):s.index("*(vinheta")]
    falas, caio, secoes = [], [], {}
    for l in corpo.splitlines():
        l = l.strip()
        if l.startswith("## "):
            secoes[l[3:].split(" (")[0].split(" — ")[0]] = len(falas)
        elif l:
            if l.startswith("🎙"):
                caio.append(len(falas)); l = l[1:].strip()
            falas.append(l)
    return falas, caio, secoes


if __name__ == "__main__":
    f, c, s = ler()
    print(s, c)
    for i, x in enumerate(f):
        print(i, x[:110])
