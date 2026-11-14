"""Trechos de filme do Ep. 09 → filmes_prontos/<nome>.mp4 (1920×1080, 30 fps, SEM áudio).
Pedido do usuário: usar cortes reais de Exhuma e A Tale of Two Sisters "bem editados", sempre com crédito.
- recorte: tira as bordas da gravação de tela (achar_cenas.py) e, nos trechos da Netflix, o logo do alto;
- câmera lenta suave (minterpolate, quadros intermediários de verdade) até ~5 s: nada de corte rápido;
- cor: um pouco menos saturada e mais escura, grão leve (casa com as imagens do episódio);
- moldura de "arquivo": o trecho menor no centro, borda fina, fundo com ele mesmo desfocado e escuro, e o crédito
  embaixo ("TRECHO DE FILME · título (ano) · direção · produtora").
O arquivo bruto (filmes/) e os prontos ficam fora do git (repositório público).
Uso: python3 cortar_filmes.py [nome ...]"""
import subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent
SAI = AQUI / "filmes_prontos"; SAI.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
IRMAS = "A TALE OF TWO SISTERS (2003) · DIR. KIM JEE-WOON · B.O.M. FILM PRODUCTIONS"
EXHUMA = "EXHUMA (2024) · DIR. JANG JAE-HYUN · SHOWBOX"
MIMIC = "THE MIMIC (2017) · DIR. HUH JUNG"
GONJIAM = "GONJIAM: HAUNTED ASYLUM (2018) · DIR. JUNG BUM-SHIK · SHOWBOX"
R = {"114623": (1920, 1030, 240, 25), "142451": (1920, 1040, 240, 20), "143012": (1920, 1040, 240, 20),
     "112939": (1636, 920, 382, 140),
     "222951": (1314, 1020, 570, 30), "223327": (1820, 1010, 340, 35)}   # v3: trailers de The Mimic e Gonjiam   # 112939 (Netflix): só a parte de baixo, sem o logo e sem a marca do título
R.update({"yt/exhuma": (1700, 800, 110, 60), "yt/tale_two_sisters": (1280, 686, 0, 18), "yt/the_wailing": (1600, 700, 160, 150),
          "yt/whispering_corridors": (520, 420, 36, 32), "yt/bunshinsaba": (1280, 700, 0, 10)})   # v4: trailers do Drive (15/11)
WHISPER = "WHISPERING CORRIDORS (1998) · DIR. PARK KI-HYUNG · CINE 2000"
WAILING = "THE WAILING (2016) · DIR. NA HONG-JIN · 20TH CENTURY FOX KOREA"
BUNSHIN = "BUNSHINSABA (2004) · DIR. AHN BYEONG-KI"
FUNDIR = {"exhuma_tambor"}
ALVO = 6.0                                                     # duração mínima depois da câmera lenta (s)
TRECHOS = {
    # v3 (14/11): só planos sem legenda gravada e sem letreiro do trailer
    "mimic_menina": ("222951", 20.4, 22.3, MIMIC),            # a menina perdida espiando na porta da casa
    "mimic_mulher": ("222951", 10.2, 11.0, MIMIC),            # reserva: a mãe olhando para fora
    "gonjiam_lanterna": ("223327", 78.3, 81.5, GONJIAM),      # a lanterna varrendo a parede no escuro do hospital
    "gonjiam_mato": ("223327", 29.6, 30.5, GONJIAM),          # o grupo com lanternas no mato, chegando ao hospital
}
V2 = {
    "irmas_deque": ("114623", 98.2, 101.3, IRMAS),           # a menina sozinha no deque do lago
    "irmas_casa": ("114623", 62.6, 65.2, IRMAS),             # a casa no capim seco (61,6–62,4 tem o ícone de carregando da gravação; 66+ ela vira o rosto)
    "exhuma_danca": ("112939", 124.8, 127.6, EXHUMA),        # a mudang Hwa-rim dançando no ritual
    "exhuma_cova": ("142451", 4.9, 6.2, EXHUMA),             # a família de preto atrás da cova aberta
    "exhuma_caixao": ("143012", 36.8, 38.1, EXHUMA),         # o caixão visto de cima, dentro da terra
    "exhuma_tambor": ("142451", 49.7, 50.6, EXHUMA),         # o tambor do ritual
    "exhuma_montanha": ("142451", 29.9, 30.7, EXHUMA),       # as montanhas
}

# 15/11 (usuário: "fazer bom uso desses trailers… um trecho tão pequeno ficou sem sentido"): SEQUÊNCIAS de verdade,
# 8–15 s, vários planos seguidos na velocidade original (sem câmera lenta), cortadas onde o próprio trailer corta;
# sem legenda gravada e sem cartela de texto. O som original sai junto em <nome>_som.wav (entra nos respiros).
V4 = {
    "irmas_chegada": ("yt/tale_two_sisters", [(2.0, 12.6), (28.0, 31.9)], IRMAS),     # a estrada, as irmãs chegando, o lago, a casa
    "wailing_vila": ("yt/the_wailing", [(3.6, 12.0)], WAILING),                      # montanhas, a vila na neblina, a fita da polícia
    "bunshin_ritual": ("yt/bunshinsaba", [(8.5, 14.6), (16.3, 18.9)], BUNSHIN),       # a caneta vermelha, a escola à noite, o papel, o corredor
    "wc_noite": ("yt/whispering_corridors", [(8.0, 23.7)], WHISPER),                 # a escola de noite: janelas, corredor, o vulto
    "exhuma_cova": ("yt/exhuma", [(6.0, 10.4), (46.0, 49.0), (50.5, 51.4)], EXHUMA), # o enterro, a cova, o caixão, o ritual, o tambor
    "exhuma_noite": ("yt/exhuma", [(90.4, 92.0), (93.0, 95.0)], EXHUMA),             # a mata de noite
}
TRECHOS.update(V2); TRECHOS.update(V4)
pedidos = sys.argv[1:] or [k for k in TRECHOS if k not in V2 and k not in V4]
for nome in pedidos:
    vid, a, b, credito = TRECHOS[nome] if len(TRECHOS[nome]) == 4 else (TRECHOS[nome][0], None, None, TRECHOS[nome][2])
    segs = TRECHOS[nome][1] if a is None else None
    if segs:   # junta os planos num arquivo só (com o som) e segue como um trecho único
        src = AQUI / "filmes" / f"{vid}.mp4"; junto = AQUI / "filmes" / f"_seq_{nome}.mp4"
        fc = "".join(f"[0:v]trim={x}:{y},setpts=PTS-STARTPTS[v{k}];[0:a]atrim={x}:{y},asetpts=PTS-STARTPTS[a{k}];" for k, (x, y) in enumerate(segs))
        fc += "".join(f"[v{k}][a{k}]" for k in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-crf", "14", "-preset", "fast", "-c:a", "pcm_s16le", str(junto.with_suffix(".mkv"))], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(junto.with_suffix(".mkv")), "-vn", "-ac", "2", "-ar", "48000",
                        str(SAI / f"{nome}_som.wav")], check=True)
        vid, a, b = f"_seq_{nome}", 0.0, sum(y - x for x, y in segs)
        R[vid] = R[TRECHOS[nome][0]]
    w, h, x, y = R[vid]
    lento = min(1.0, (b - a) / ALVO)                           # 1 = velocidade normal
    fator = 1 / lento
    fw, fh = 1536, 864                                         # o trecho dentro da moldura (80%)
    fx, fy = (1920 - fw) // 2, 120                            # crédito EM CIMA: embaixo a legenda cobria
    # movimento rápido (baquetas) deforma na interpolação por movimento: ali o quadro funde no seguinte (borrão suave)
    interp = ("fps=30" if vid.startswith("_seq_") and lento >= 1 else "minterpolate=fps=30:mi_mode=blend" if nome in FUNDIR else
              "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
    cor = "eq=saturation=0.82:contrast=1.06:brightness=-0.03,noise=alls=7:allf=t"
    filtro = (
        f"[0:v]crop={w}:{h}:{x}:{y},scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
        + ("" if vid.startswith("_seq_") else "mpdecimate,setpts=N/24/TB,") +
        # rascunho 1 "travando": a gravação repetia quadros irregularmente (mpdecimate volta a 24 q/s regulares)
        f"setpts={fator:.4f}*PTS,{interp},{cor},split[a][b];"
        f"[a]scale=480:270,boxblur=12:3,eq=brightness=-0.22:saturation=0.6,scale=1920:1080[fundo];"
        f"[b]scale={fw}:{fh},pad={fw + 4}:{fh + 4}:2:2:color=0xb8b0a4@0.55[quadro];"
        f"[fundo][quadro]overlay={fx - 2}:{fy - 2},"
        f"drawtext=fontfile={FONTE}:text='TRECHO DE FILME':fontsize=22:fontcolor=0xc8302c:x={fx}:y={fy - 46},"
        f"drawtext=fontfile={FONTE}:text='{credito}':fontsize=22:fontcolor=0xd8d0c4:x={fx + 230}:y={fy - 46},"
        f"format=yuv420p[v]"
    )
    saida = SAI / f"{nome}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.2f}", "-t", f"{b - a:.2f}",
                    "-i", str(AQUI / "filmes" / (f"{vid}.mkv" if vid.startswith("_seq_") else f"{vid}.mp4" if vid.startswith("yt/") else f"screen-20261113-{vid}.mp4")), "-filter_complex", filtro, "-map", "[v]",
                    "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(saida)], check=True)
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(saida)],
                             capture_output=True, text=True).stdout)
    print(f"ok {nome}: {b - a:.1f}s → {d:.1f}s ({lento:.2f}×)", flush=True)
    # 14/11: folha de conferência (um quadro a cada 0,4 s do trecho pronto) — olhar ANTES de usar: ícone de
    # carregando da gravação, legenda gravada, logo, letreiro, rosto cortado, quadro deformado pela câmera lenta
    from PIL import Image
    qs = []
    for k in range(int(d / 0.4)):
        tmpq = SAI / "_q.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{k * 0.4:.2f}", "-i", str(saida), "-frames:v", "1",
                        "-vf", "scale=320:-2", str(tmpq)], check=True)
        qs.append(Image.open(tmpq).copy())
    if qs:
        cols = 6; h = qs[0].height
        folha = Image.new("RGB", (320 * cols, h * ((len(qs) + cols - 1) // cols)))
        for k, q in enumerate(qs):
            folha.paste(q, ((k % cols) * 320, (k // cols) * h))
        folha.save(SAI / f"{nome}_conferir.jpg", quality=80)
