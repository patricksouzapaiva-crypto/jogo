"""Os 4 cartões de capítulo do Ep. 10 no motor 3D (painel/cartao3d, three.js), 16/11. Cada cartão sai como vídeo
pronto em cartoes/cap<N>.mp4 (com o som: a música do capítulo + o pano desenrolando), para entrar na montagem como cena
de vídeo. Também monta a prévia com os 4 em sequência sobre a trilha unida.
Uso: python3 cartoes.py [N ...]   (sem números: todos os que faltam) ; --previa só remonta a prévia"""
import json, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent; PAINEL = AQUI.parents[1] / "painel"; SONS = PAINEL / "sons"
(AQUI / "cartoes").mkdir(exist_ok=True); (AQUI / "previas").mkdir(exist_ok=True)
DUR = 7.6
CAPS = {
    1: {"titulo": "O aluguel da terra e os famintos", "ano": "Século XIX → hoje", "cor": "vermelho"},
    2: {"titulo": "As criaturas da noite", "ano": "Folclore rural de Isan", "cor": "vermelho"},
    3: {"titulo": "Os corpos emprestados e a magia proibida", "ano": "A tradição Rang Song", "cor": "branco"},
    4: {"titulo": "Quando a câmera entrou na floresta", "ano": "Loei · 2021", "cor": "vermelho"},
}
pedidos = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(CAPS)
if "--previa" not in sys.argv:
    for n in pedidos:
        mudo, final = Path("/tmp") / f"ep10_cap{n}_mudo.mp4", AQUI / "cartoes" / f"cap{n}.mp4"   # o mudo é temporário (disco)
        if not mudo.exists() or str(n) in sys.argv[1:]:
            cfg = {"numero": n, "numero_pt": f"Capítulo {n}", "dur": DUR, **CAPS[n]}
            subprocess.run(["node", str(PAINEL / "cartao3d" / "render_cartao.js"), json.dumps(cfg, ensure_ascii=False), str(mudo)], check=True)
        # som do cartão: música do capítulo (o tambor dela bate em 1.6 s, junto com o tranco) + o pano desenrolando
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mudo), "-i", str(SONS / f"ep10_cap{n}.mp3"), "-i", str(SONS / "ep10_desenrolar.mp3"),
                        "-filter_complex", "[1]aformat=channel_layouts=stereo,afade=t=out:st=6.6:d=1[m];[2]aformat=channel_layouts=stereo,adelay=100|100,volume=-4dB[d];"
                        "[m][d]amix=inputs=2:normalize=0,apad[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", str(final)], check=True)
        print("ok", final.name)
# prévia: os 4 cartões em sequência, separados por 3 s da trilha (como no episódio: narração → cartão → narração)
prontos = [AQUI / "cartoes" / f"cap{n}.mp4" for n in CAPS if (AQUI / "cartoes" / f"cap{n}.mp4").exists()]
if prontos:
    ins, f = [], []
    for k, p in enumerate(prontos):
        ins += ["-i", str(p)]
        f.append(f"[{k}:v]tpad=stop_mode=add:stop_duration=2.4:color=black[v{k}];[{k}:a]apad=pad_dur=2.4[a{k}]")
    cat = "".join(f"[v{k}][a{k}]" for k in range(len(prontos)))
    tot = len(prontos) * (DUR + 2.4)
    ins += ["-i", str(AQUI / "trilha" / "previa_unida.mp3")]
    f.append(f"{cat}concat=n={len(prontos)}:v=1:a=1[v][c];[{len(prontos)}:a]atrim=0:{tot},volume=-15dB,afade=t=out:st={tot - 2}:d=2[b];[c][b]amix=inputs=2:normalize=0,alimiter=limit=0.9[a]")
    saida = AQUI / "previas" / "cartoes_3d.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(f), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18",
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(saida)], check=True)
    print("prévia:", saida)
