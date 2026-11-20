"""Trechos de filme do Ep. 11 → filmes_prontos/<nome>.mp4 (1920×1080, SEM áudio, na taxa de quadros original).
20/11: o usuário subiu no Drive os trailers oficiais de O Ritual (Netflix) e Midsommar (A24) e cenas avulsas.
- sequências de 6–10 s, vários planos seguidos na velocidade original, cortadas onde o próprio trailer corta;
  sem cartela de texto, sem close de rosto, e a criatura do filme só em silhueta;
- recorte tira a marca da Netflix (canto de baixo) e as faixas pretas;
- cor um pouco menos saturada e mais escura, grão leve (casa com as imagens do episódio);
- moldura de "arquivo": o trecho menor no centro, fundo com ele mesmo desfocado, crédito em cima;
- a taxa de quadros fica a original (24 q/s): o motor passa pelo RIFE e chega a 30 sem tranco.
Os arquivos (filmes/ e filmes_prontos/) ficam fora do git (repositório público).
Uso: python3 cortar_filmes.py [nome ...]"""
import subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent
SAI = AQUI / "filmes_prontos"; SAI.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
RITUAL = "THE RITUAL (2017) · DIR. DAVID BRUCKNER · NETFLIX"
MIDS = "MIDSOMMAR (2019) · DIR. ARI ASTER · A24"
# arquivo → recorte (w, h, x, y) na resolução original
R = {"ritual_trailer": (1600, 900, 40, 40), "ritual_criatura": (1920, 800, 0, 140),     # 1600×900: fora a marca NETFLIX
     "midsommar_trailer": (1920, 1080, 0, 0), "midsommar_penhasco": (1280, 720, 0, 0)}
# (início, fim[, lento]): os cortes caem nos cortes do próprio trailer (ffmpeg scene). lento > 1: plano curto do trailer
# em câmera lenta pelo RIFE (usuário: "sem pulos de imagem rápido onde a pessoa nem entende que imagem é")
TRECHOS = {
    "ritual_floresta": ("ritual_trailer", [(31.0, 33.5), (34.7, 38.5)], RITUAL),            # a floresta de cima, o chão da mata
    "ritual_amigos": ("ritual_trailer", [(12.2, 14.2), (18.95, 19.8, 2.0), (23.95, 26.65)], RITUAL),   # os amigos de costas, a borda da floresta
    "ritual_jotunn": ("ritual_criatura", [(10.35, 13.0), (14.5, 17.4)], RITUAL),           # o Jötunn em silhueta contra o fogo, a cabana ardendo
    "mids_portal": ("midsommar_trailer", [(60.5, 62.4), (64.6, 67.5)], MIDS),               # o portal do sol, a chegada à comuna
    "mids_comuna": ("midsommar_trailer", [(72.6, 77.4), (80.4, 83.0)], MIDS),               # os campos de Hårga, gente de branco
    "mids_danca": ("midsommar_trailer", [(95.3, 96.4, 2.5), (98.6, 99.6, 2.5), (136.6, 139.2)], MIDS),   # o violinista e a roda, as coroas de flores
    "mids_penhasco": ("midsommar_penhasco", [(58.0, 64.8)], MIDS),                          # o ancião no alto do penhasco (nunca a queda)
}
sys.path.insert(0, str(AQUI.parents[1] / "painel" / "ferramentas"))
from interpolar import interpolar   # noqa: E402
TMP = SAI / "_tmp"; TMP.mkdir(exist_ok=True)
for nome in sys.argv[1:] or list(TRECHOS):
    vid, segs, credito = TRECHOS[nome]
    w, h, x, y = R[vid]
    fw, fh = 1536, 864; fx, fy = (1920 - fw) // 2, 120
    cor = "eq=saturation=0.8:contrast=1.06:brightness=-0.03,noise=alls=7:allf=t"
    # cada plano vira um arquivo (24 q/s); os curtos passam pelo RIFE em câmera lenta; depois são unidos
    partes = []
    for k, sg in enumerate(segs):
        a, b = sg[0], sg[1]; lento = sg[2] if len(sg) > 2 else 1.0
        pq = TMP / f"{nome}_{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(AQUI / "filmes" / f"{vid}.mp4"),
                        "-an", "-vf", "fps=24", "-c:v", "libx264", "-crf", "14", "-preset", "fast", str(pq)], check=True)
        if lento > 1:
            lt = TMP / f"{nome}_{k}_lento.mp4"; interpolar(pq, lt, lento=lento, fps=24); pq = lt
        partes.append(pq)
    ent = sum((["-i", str(x)] for x in partes), [])
    fc = "".join(f"[{k}:v]setpts=PTS-STARTPTS,fps=24[s{k}];" for k in range(len(partes)))
    fc += "".join(f"[s{k}]" for k in range(len(partes))) + f"concat=n={len(partes)}:v=1:a=0[c];"
    fc += (f"[c]crop={w}:{h}:{x}:{y},scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,{cor},split[a][b];"
           f"[a]scale=480:270,boxblur=12:3,eq=brightness=-0.22:saturation=0.6,scale=1920:1080[fundo];"
           f"[b]scale={fw}:{fh},pad={fw + 4}:{fh + 4}:2:2:color=0xb8b0a4@0.55[quadro];"
           f"[fundo][quadro]overlay={fx - 2}:{fy - 2},"
           f"drawtext=fontfile={FONTE}:text='TRECHO DE FILME':fontsize=22:fontcolor=0xc8302c:x={fx}:y={fy - 46},"
           f"drawtext=fontfile={FONTE}:text='{credito}':fontsize=22:fontcolor=0xd8d0c4:x={fx + 230}:y={fy - 46},format=yuv420p[v]")
    saida = SAI / f"{nome}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", fc,
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "17", "-preset", "medium", str(saida)], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(saida)],
                             capture_output=True, text=True).stdout)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida), "-vf", f"fps=1/{max(0.5, d / 12):.2f},scale=320:-2,tile=6x2",
                    "-frames:v", "1", str(SAI / f"{nome}_conferir.jpg")], check=True)
    print(f"ok {nome}: {d:.1f}s", flush=True)
    for x in TMP.glob(f"{nome}_*"): x.unlink()
