"""Trechos do filme para os Shorts (23/11, pedido do usuário: "cenas do filme nos shorts, isso vitaliza muito").
Formato vertical de Short de filme: o fundo é o próprio quadro ampliado e desfocado; o filme fica no meio (760 px de altura, laterais cortadas),
com o crédito em cima e a fala (amarela, itálico) embaixo. Sem espelhar, cortar ou mudar a cor para esconder do Content ID:
o usuário sabe que o Short pode ser reivindicado/bloqueado pela NBC Universal.
Saída: shorts/filme_<nome>.mp4 (+ shorts/filme_<nome>.wav quando tem fala). Uso: python3 cortar_vertical.py"""
import subprocess
from pathlib import Path

AQUI = Path(__file__).parent
FILME = AQUI / "filme" / "outra_mamae.mkv"
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTE_FALA = "/usr/share/fonts/opentype/inter/Inter-SemiBoldItalic.otf"
CREDITO = "OUTRA MAMÃE (2026) · UNIVERSAL PICTURES"
SAI = AQUI / "shorts"
# nome: (início no filme, duração, [(de, até, fala)], com_som)
CLIPES = {
    "caso_cheiro": (909.5, 3.1, [(0.45, 2.75, "Você está com o cheiro de outra pessoa.")], True),
    "p6_existir": (1721.8, 3.6, [(0.38, 3.17, "Dói muito, Bela. Eu preciso existir.")], True),
    "p7_eu": (3017.3, 3.6, [(0.46, 3.22, "Eu vou ser você e você será eu.")], True),
    "b_outra_rosto": (592.5, 9.0, [], False),
    "b_pais_briga": (760.0, 9.0, [], False),
    "b_bela_sozinha": (386.0, 9.0, [], False),
    "b_rosto_final": (4895.0, 9.0, [], False),
    "b_mesa": (700.0, 7.5, [], False),
}


def esc(t):
    return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%").replace(",", "\\,")


def quebrar(t, n=24):
    out, linha = [], ""
    for p in t.split():
        if linha and len(linha) + 1 + len(p) > n:
            out.append(linha); linha = p
        else:
            linha = (linha + " " + p).strip()
    return out + [linha]


for nome, (a, d, falas, som) in CLIPES.items():
    fh = 760; fy = (1920 - fh) // 2 - 80   # o filme maior (corta as laterais do 2,2:1): no celular o quadro inteiro ficava miúdo
    txt = ""
    for x, y, t in falas:
        for k, l in enumerate(quebrar(t)):
            txt += (f",drawtext=fontfile={FONTE_FALA}:text='{esc(l)}':fontsize=62:fontcolor=0xffd75e:box=1:boxcolor=0x000000@0.6"
                    f":boxborderw=16:x=(w-text_w)/2:y={fy + fh + 70 + k * 92}:enable='between(t,{x:.2f},{y:.2f})'")
    fc = (f"[0:v]setpts=PTS-STARTPTS,eq=gamma=1.1:saturation=0.9,split[a][b];"
          f"[a]scale=-2:1920,crop=1080:1920,boxblur=24:4,eq=brightness=-0.25:saturation=0.7[fundo];"
          f"[b]scale=-2:{fh},crop=1080:{fh}[quadro];[fundo][quadro]overlay=0:{fy},"
          f"drawtext=fontfile={FONTE}:text='{esc(CREDITO)}':fontsize=30:fontcolor=0xd8d0c4:x=(w-text_w)/2:y={fy - 52}{txt},"
          f"format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", str(FILME), "-filter_complex", fc,
                    "-map", "[v]", "-an", "-r", "24", "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(SAI / f"filme_{nome}.mp4")],
                   check=True)
    if som:   # a dublagem no canal central, como nos trechos do vídeo longo
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", str(FILME), "-map", "0:1", "-af",
                        f"pan=stereo|FL=FC+0.45*FL+0.3*BL+0.3*SL|FR=FC+0.45*FR+0.3*BR+0.3*SR,loudnorm=I=-18:TP=-2:LRA=11,"
                        f"afade=t=in:d=0.2,afade=t=out:st={d - 0.35:.2f}:d=0.35", "-ar", "48000", "-ac", "2",
                        str(SAI / f"filme_{nome}.wav")], check=True)
    print("ok", nome)
