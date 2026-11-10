"""Gera legenda .srt (para enviar ao YouTube) a partir do <video>.tempos.json que o gerar.py grava ao lado do vídeo.
Blocos de até ~7 palavras / 42 caracteres, quebrando em fim de frase ou vírgula; cada bloco dura até a próxima fala.
Uso: python3 gerar_srt.py video.mp4.tempos.json saida.srt [--fim=SEGUNDOS]
"""
import json
import sys


def hms(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"


def blocos(palavras, max_pal=7, max_car=42):
    atual, out = [], []
    for w, s, e in palavras:
        atual.append((w, s, e))
        texto = " ".join(x[0] for x in atual)
        fim_frase = w.endswith((".", "?", "!", "…", '."', '?"', '…"'))
        pausa = w.endswith((",", ":", ";"))
        if fim_frase or len(atual) >= max_pal or len(texto) >= max_car or (pausa and len(atual) >= 3):
            out.append(atual)
            atual = []
    if atual:
        out.append(atual)
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    fim = next((float(x.split("=")[1]) for x in sys.argv if x.startswith("--fim=")), None)
    P = json.load(open(a[0], encoding="utf-8"))["palavras"]
    bl = blocos(P)
    linhas = []
    for i, b in enumerate(bl):
        t0 = b[0][1]
        prox = bl[i + 1][0][1] if i + 1 < len(bl) else (fim or b[-1][2] + 1.5)
        t1 = min(max(b[-1][2] + 0.4, t0 + 0.8), prox - 0.05)
        texto = " ".join(w for w, _, _ in b).replace('"', "")
        linhas.append(f"{i + 1}\n{hms(t0)} --> {hms(t1)}\n{texto}\n")
    open(a[1], "w", encoding="utf-8").write("\n".join(linhas))
    print(f"{len(linhas)} legendas -> {a[1]}")


if __name__ == "__main__":
    main()
