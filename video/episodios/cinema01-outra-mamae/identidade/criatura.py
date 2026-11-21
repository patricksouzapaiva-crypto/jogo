"""O QUE É A CRIATURA? — a mesa de investigação animada (21/11).
Usuário: "gerar imagens separadas bem feitas e você fazer a animação… algo com maior qualidade". As camadas vêm do
Drive (identidade/brutas → recortar.py → identidade/camadas) e cada peça do formato é montada aqui, quadro a quadro,
com câmera (zoom, giro, tremida), sombra que cresce quando o objeto sobe da mesa, desfoque de movimento, luz da
luminária que pisca, tinta de carimbo com falhas, texto de máquina de escrever e grão de filme.
Peças: abertura (vinheta do formato). Uso: python3 criatura.py abertura saida.mp4"""
from pathlib import Path
import math, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
EP = AQUI.parent
CAM = AQUI / "camadas"
FONTES = Path(__file__).resolve().parents[3] / "painel" / "fontes"
SONS = Path(__file__).resolve().parents[3] / "painel" / "sons"
W, H, FPS = 1920, 1080, 30
TINTA = np.array([28, 24, 150], np.float32) / 255     # vermelho do carimbo (BGR)
rng = np.random.default_rng(3)


# ------------------------------------------------------------------ utilidades
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def eout(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def ein(x): x = min(max(x, 0.0), 1.0); return x ** 3
def lin(t, a, d): return min(max((t - a) / d, 0.0), 1.0)
def back(x, s=1.4): x = min(max(x, 0.0), 1.0); x -= 1; return x * x * ((s + 1) * x + s) + 1


def carregar(nome):
    im = cv2.imread(str(CAM / nome), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    if im.shape[2] == 3:
        im = np.dstack([im, np.ones(im.shape[:2], np.float32)])
    im[..., :3] *= im[..., 3:4]          # pré-multiplicado
    return im


def de_pil(img):
    a = np.asarray(img.convert("RGBA")).astype(np.float32) / 255
    a = a[..., [2, 1, 0, 3]].copy(); a[..., :3] *= a[..., 3:4]
    return a


def mat_cam(cx, cy, z, rot):
    c, s = math.cos(math.radians(rot)) * z, math.sin(math.radians(rot)) * z
    return np.array([[c, -s, W / 2 - c * cx + s * cy], [s, c, H / 2 - s * cx - c * cy], [0, 0, 1]], np.float32)


def mat_obj(x, y, esc, ang, w, h, sx=1.0, ancora=(0.5, 0.5)):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)
    S = np.diag([esc * sx, esc, 1]).astype(np.float32)
    T0 = np.array([[1, 0, -w * ancora[0]], [0, 1, -h * ancora[1]], [0, 0, 1]], np.float32)
    T1 = np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float32)
    return T1 @ R @ S @ T0


def por(tela, img, M, alfa=1.0, sombra=0.0, z=0.0):
    """Desenha a camada (pré-multiplicada) com a matriz M (3×3, já com a câmera). z = altura sobre a mesa:
    a sombra se afasta e borra quando o objeto sobe."""
    if alfa <= 0.001:
        return
    camada = cv2.warpAffine(img, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    if sombra > 0:
        d = 6 + z * 38; sig = 4 + z * 22
        Ms = M.copy(); Ms[0, 2] += d * 0.55; Ms[1, 2] += d
        a = cv2.warpAffine(img[..., 3], Ms[:2], (W, H))
        a = cv2.GaussianBlur(a, (0, 0), sig) * sombra * (0.75 - 0.35 * min(z, 1)) * alfa
        tela *= (1 - a[..., None])
    tela[:] = tela * (1 - camada[..., 3:4] * alfa) + camada[..., :3] * alfa


def texto_img(txt, fonte, tam, cor=(20, 18, 16), largura=None, espaco=1.0):
    f = ImageFont.truetype(str(FONTES / fonte), tam)
    linhas = txt.split("\n")
    ws = [f.getbbox(l)[2] for l in linhas] or [1]
    w = largura or max(ws) + 20; h = int(len(linhas) * tam * 1.25 * espaco) + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, l in enumerate(linhas):
        d.text((10, 10 + k * tam * 1.25 * espaco), l, font=f, fill=cor + (255,))
    return im


def tinta_carimbo(linhas, larg=1100):
    """Texto de carimbo: letras vermelhas com falhas de tinta, borda irregular e moldura dupla."""
    f1 = ImageFont.truetype(str(FONTES / "StardosStencil-Bold.ttf"), 92)
    f2 = ImageFont.truetype(str(FONTES / "StardosStencil-Bold.ttf"), 210)
    w = larg; h = 420
    im = Image.new("L", (w, h), 0); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, w - 8, h - 8), 26, outline=255, width=12)
    d.rounded_rectangle((34, 34, w - 34, h - 34), 18, outline=255, width=5)
    t1 = linhas[0]; t2 = linhas[1]
    d.text(((w - d.textlength(t1, font=f1)) / 2, 52), t1, font=f1, fill=255)
    d.text(((w - d.textlength(t2, font=f2)) / 2, 128), t2, font=f2, fill=255)
    a = np.asarray(im).astype(np.float32) / 255
    ruido = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 2.2)
    ruido2 = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 14)
    a = a * np.clip((ruido - 0.36) * 4 + (ruido2 - 0.5) * 2.5 + 0.55, 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 0.7)
    return np.clip(a * 0.92, 0, 1)


def grade_foto(img, sepia=0.55, contraste=1.1):
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255
    g = a.mean(2, keepdims=True)
    sep = np.concatenate([g * 1.07, g * 0.95, g * 0.78], 2)
    a = a * (1 - sepia) + sep * sepia
    a = np.clip((a - 0.5) * contraste + 0.5, 0, 1)
    hh, ww = a.shape[:2]; yy, xx = np.mgrid[0:hh, 0:ww]
    v = 1 - 0.45 * (((xx - ww / 2) / ww) ** 2 + ((yy - hh / 2) / hh) ** 2) * 2.2
    return Image.fromarray((np.clip(a * v[..., None], 0, 1) * 255).astype(np.uint8))


def polaroide(foto, base="ID06_polaroide_1.png"):
    """A foto dentro da janela preta da polaroide (a janela é achada pela cor)."""
    pol = Image.open(CAM / base).convert("RGBA"); a = np.asarray(pol)
    preto = (a[..., :3].max(2) < 40) & (a[..., 3] > 200)
    ys, xs = np.where(preto); y0, y1, x0, x1 = ys.min() + 2, ys.max() - 2, xs.min() + 2, xs.max() - 2
    fw, fh = x1 - x0, y1 - y0
    iw, ih = foto.size; k = max(fw / iw, fh / ih)
    f = foto.resize((int(iw * k) + 1, int(ih * k) + 1), Image.LANCZOS)
    f = f.crop(((f.width - fw) // 2, (f.height - fh) // 2, (f.width - fw) // 2 + fw, (f.height - fh) // 2 + fh))
    pol.paste(f, (x0, y0))
    return de_pil(pol)


def recorte_jornal(img, larg=700):
    """Recorte de jornal: papel amarelado, borda rasgada."""
    im = img.convert("L"); k = larg / im.width; im = im.resize((larg, int(im.height * k)), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255
    papel = np.stack([a * 0.80 + 0.06, a * 0.88 + 0.05, a * 0.93 + 0.05], 2)   # BGR amarelado
    hh, ww = a.shape
    al = np.ones((hh, ww), np.float32)
    for borda in range(4):    # rasgado: ruído na borda
        n = (hh if borda < 2 else ww)
        prof = np.clip(cv2.GaussianBlur(rng.random((n, 1)).astype(np.float32), (0, 0), 3)[:, 0] * 22, 2, 30).astype(int)
        for i, p in enumerate(prof):
            if borda == 0: al[i, :p] = 0
            elif borda == 1: al[i, ww - p:] = 0
            elif borda == 2: al[:p // 2, i] = 0
            else: al[hh - p // 2:, i] = 0
    al = cv2.GaussianBlur(al, (0, 0), 0.8)
    out = np.dstack([papel * al[..., None], al])
    return out.astype(np.float32)


def fio(tela, pts, prog, M):
    """Linha vermelha entre as tachinhas, com barriga, desenhada até 'prog' (0–1) do comprimento."""
    cam = []
    for (a, b) in zip(pts[:-1], pts[1:]):
        for k in range(24):
            u = k / 23; x = a[0] + (b[0] - a[0]) * u; y = a[1] + (b[1] - a[1]) * u + math.sin(math.pi * u) * 26
            cam.append((x, y))
    n = max(2, int(len(cam) * prog))
    p = np.array(cam[:n], np.float32)
    p = (M[:2, :2] @ p.T).T + M[:2, 2]
    if len(p) < 2:
        return
    camada = np.zeros((H, W), np.float32)
    cv2.polylines(camada, [p.astype(np.int32)], False, 1.0, 4, cv2.LINE_AA)
    sombra = cv2.GaussianBlur(np.roll(np.roll(camada, 7, 0), 4, 1), (0, 0), 3) * 0.5
    tela *= (1 - sombra[..., None])
    cor = np.array([30, 25, 170], np.float32) / 255
    tela[:] = tela * (1 - camada[..., None]) + cor * camada[..., None]


def virar(tela, C, teta, frente, verso, xs, yc, w, h, centro):
    """Capa da pasta girando na lombada (eixo vertical em x = xs), em 3D com perspectiva: a borda livre sobe em
    direção à câmera (fica maior), a capa escurece de perfil, mostra o verso depois dos 90° e projeta sombra."""
    th = math.radians(teta); co, si = math.cos(th), max(0.0, math.sin(th))
    xf = xs + w * co; z = w * si
    p = 2600 / (2600 - z * 0.9)
    def proj(x, y): return (centro[0] + (x - centro[0]) * p, centro[1] + (y - centro[1]) * p)
    mundo = [(xs, yc - h / 2), (xs, yc + h / 2), proj(xf, yc - h / 2), proj(xf, yc + h / 2)]
    tela_pts = [tuple((C @ np.array([x, y, 1], np.float32))[:2]) for x, y in mundo]
    # sombra na mesa / na página de baixo
    if si > 0.01:
        sx_ = xs + w * co + z * 0.35; som = [(xs, yc - h / 2), (xs, yc + h / 2), (sx_, yc + h / 2 + z * 0.25), (sx_, yc - h / 2 + z * 0.25)]
        pts = np.array([(C @ np.array([x, y, 1], np.float32))[:2] for x, y in som], np.float32)
        a = np.zeros((H, W), np.float32); cv2.fillConvexPoly(a, pts.astype(np.int32), 1.0, cv2.LINE_AA)
        a = cv2.GaussianBlur(a, (0, 0), 6 + z * 0.04) * 0.5 * si
        tela *= (1 - a[..., None])
    img = frente if teta <= 90 else verso
    h0, w0 = img.shape[:2]
    src = np.float32([(0, 0), (0, h0), (w0, 0), (w0, h0)]) if teta <= 90 else np.float32([(w0, 0), (w0, h0), (0, 0), (0, h0)])
    Mp = cv2.getPerspectiveTransform(src, np.float32(tela_pts))
    cam = cv2.warpPerspective(img, Mp, (W, H), flags=cv2.INTER_LINEAR)
    luz_c = 0.62 + 0.38 * abs(co) + (0.06 * si if teta > 90 else 0)
    tela[:] = tela * (1 - cam[..., 3:4]) + cam[..., :3] * luz_c


def luz(t, cx, cy, z, rot):
    """Poça de luz quente da luminária (presa à mesa) + pisca leve."""
    M = mat_cam(cx, cy, z, rot)
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32) * 4
    inv = np.linalg.inv(M); wx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; wy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]
    d = ((wx - 980) / 900) ** 2 + ((wy - 560) / 620) ** 2
    pisca = 1 + 0.035 * math.sin(t * 13.1) + 0.025 * math.sin(t * 31.7) - (0.18 if 0.3 < (t * 7.3) % 9 < 0.5 else 0)
    L = (0.55 + 0.85 * np.exp(-d * 1.3)) * pisca
    return cv2.resize(L.astype(np.float32), (W, H))


def acabamento(tela, L, t, fim):
    img = tela * L[..., None]
    img = img * np.array([0.86, 0.97, 1.10], np.float32)        # quente (BGR)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.55 * np.clip(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2 - 0.15, 0, 1)
    img = img * v[..., None]
    img += (rng.standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)) * 0.022
    f = min(lin(t, 0, 0.5), 1 - lin(t, fim - 0.6, 0.6))
    return (np.clip(img * f, 0, 1) * 255).astype(np.uint8)


# ------------------------------------------------------------------ peça: abertura do formato
LENTO = 1.4   # 21/11 (usuário: "um pouco menos rápido, pra que seja possível entender tudo"): tudo 40% mais lento


def abertura(saida, num="1", filme="OUTRA MAMÃE", ano="2026"):
    DUR = 11.2    # tempo da animação (o vídeo dura DUR × LENTO); o último segundo é só o título parado
    mesa = carregar("ID01_mesa_1.png"); mesa_M = mat_obj(960, 540, 2300 / mesa.shape[1], 0, mesa.shape[1], mesa.shape[0])
    lupa = carregar("ID08_lupa_1.png"); filme_t = carregar("ID09_filme_1.png")
    fechada0 = Image.open(CAM / "ID04_pasta_fechada_1.png").convert("RGBA")
    aberta = carregar("ID05_pasta_aberta_1.png")
    pino_src = Image.open(CAM / "ID10_tachinhas_1.png").convert("RGBA")
    pw = pino_src.width // 3; pino = de_pil(pino_src.crop((0, 0, int(pw * 0.95), pino_src.height)))
    carimbo = carregar("ID11_carimbo_1.png")
    ficha0 = Image.open(CAM / "ID07_ficha_2.png").convert("RGBA")
    from PIL import ImageEnhance
    polA = polaroide(grade_foto(ImageEnhance.Brightness(Image.open(AQUI / "brutas" / "ID20_outra_mamae_1.png")).enhance(2.3), 0.3, 1.1))
    polB = polaroide(grade_foto(Image.open(EP / "reais" / "new_mother_n26.jpg").crop((58, 421, 1952, 3018)), 0.6), "ID06_polaroide_2.png")
    jornal = recorte_jornal(Image.open(EP / "reais" / "cleary_sun_1895.jpg").crop((25, 0, 760, 1500)))
    tinta = tinta_carimbo(["O QUE É A", "CRIATURA?"])
    # etiqueta da pasta: texto datilografado letra a letra
    rot1, rot2 = f"ARQUIVO Nº {num}", filme
    lab = np.asarray(fechada0).astype(int)
    sat, mx = lab[..., :3].max(2) - lab[..., :3].min(2), lab[..., :3].max(2)
    claro = ((sat < 75) & (mx > 150) & (lab[..., 3] > 200)).astype(np.uint8)          # a etiqueta: creme, pouco saturada
    claro = cv2.morphologyEx(claro, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    nb, labb, stb, _ = cv2.connectedComponentsWithStats(claro)
    kb = 1 + int(np.argmax(stb[1:, cv2.CC_STAT_AREA]))
    ex0, ey0 = stb[kb, 0], stb[kb, 1]; ex1, ey1 = ex0 + stb[kb, 2], ey0 + stb[kb, 3]
    cache = {}

    def fechada_com(n):
        if n not in cache:
            im = fechada0.copy(); d = ImageDraw.Draw(im)
            f1 = ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), int((ey1 - ey0) * 0.27))
            larg_max = (ex1 - ex0) - 30; tam2 = int((ey1 - ey0) * 0.36)
            while ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), tam2).getbbox(rot2)[2] > larg_max: tam2 -= 2
            f2 = ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), tam2)
            a, b = rot1[:n], rot2[:max(0, n - len(rot1))]
            d.text((ex0 + 16, ey0 + (ey1 - ey0) * 0.10), a, font=f1, fill=(34, 28, 24, 235))
            d.text((ex0 + 16, ey0 + (ey1 - ey0) * 0.52), b, font=f2, fill=(34, 28, 24, 245))
            cache[n] = de_pil(im)
        return cache[n]

    ficha_txt = f"O QUE É A CRIATURA? · ARQUIVO Nº {num}\n{filme} ({ano})"
    cache_f = {}

    def ficha_com(n):
        if n not in cache_f:
            im = ficha0.copy(); d = ImageDraw.Draw(im)
            lin1, lin2 = ficha_txt.split("\n")
            fw0 = ficha0.width - 140
            t1 = 60
            while ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), t1).getbbox(lin1)[2] > fw0: t1 -= 2
            t2 = 110
            while ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), t2).getbbox(lin2)[2] > fw0: t2 -= 2
            d.text((70, ficha0.height * 0.2), lin1[:n], font=ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), t1), fill=(30, 26, 24, 240))
            d.text((70, ficha0.height * 0.45), lin2[:max(0, n - len(lin1))], font=ImageFont.truetype(str(FONTES / "SpecialElite-Regular.ttf"), t2), fill=(30, 26, 24, 245))
            cache_f[n] = de_pil(im)
        return cache_f[n]

    # posições no mundo (1920×1080)
    esc_f = 600 / fechada0.height
    FX, FY = 960 + fechada0.width * esc_f / 2, 560      # a lombada (borda esquerda da fechada) fica no centro
    esc_a = (fechada0.height * esc_f * 0.98) / aberta.shape[0]
    meio = aberta.shape[1] // 2      # as duas páginas da pasta aberta, cada uma do tamanho exato da capa fechada
    pag_esq = cv2.resize(aberta[:, :meio], (fechada0.width, fechada0.height), interpolation=cv2.INTER_AREA)
    pag_dir = cv2.resize(aberta[:, meio:], (fechada0.width, fechada0.height), interpolation=cv2.INTER_AREA)
    wf, hf = fechada0.width * esc_f, fechada0.height * esc_f
    largA = aberta.shape[1] * esc_a; espinha = FX - fechada0.width * esc_f / 2   # lombada: borda esquerda da fechada
    AX = espinha                              # centro da aberta = lombada
    tA, tJ, tB = 4.3, 4.6, 4.9
    PA = (AX - 300, FY - 95, 360 / polA.shape[0], -6)
    PJ = (AX + 150, FY - 120, 205 / jornal.shape[1], 3.5)
    PB = (AX + 450, FY - 150, 260 / polB.shape[0], 9)
    pinos = [(PA[0] + 8, PA[1] - 157), (PJ[0], PJ[1] - 0.5 * jornal.shape[0] * PJ[2] + 18), (PB[0] - 5, PB[1] - 115)]
    tt = len(rot1) + len(rot2); tf = len(ficha_txt) - 1
    sons = []
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", str(saida) + ".v.mp4"],
                            stdin=subprocess.PIPE)
    n_q = int(DUR * LENTO * FPS)
    so = [int(float(x) * FPS * LENTO) for x in PREVIA] if PREVIA else None
    for q in range(n_q):
        t = q / FPS / LENTO
        if so is not None and q not in so:
            continue
        # câmera: começa perto da mesa vazia, aproxima da etiqueta, recua para a pasta aberta, treme no carimbo
        k1 = ease(lin(t, 1.1, 1.2)); k2 = ease(lin(t, 2.8, 0.85)); k3 = ease(lin(t, 7.6, 2.6)) * 0.4
        cx = 1000 + (FX - 1000) * k1 * (1 - k2) + (980 - 1000) * k2
        cy = 560 + (FY - 560 - 150) * k1 * (1 - k2) + (40) * k2
        z = 1.12 + 0.55 * k1 * (1 - k2) - 0.06 * k2 + 0.05 * k3
        rot = 1.5 - 1.5 * k2 + 0.4 * math.sin(t * 0.5)
        tre = max(0.0, 1 - (t - 7.0) / 0.45) if t >= 7.0 else 0.0
        cx += math.sin(t * 90) * 14 * tre; cy += math.cos(t * 77) * 10 * tre
        C = mat_cam(cx, cy, z, rot)
        tela = np.zeros((H, W, 3), np.float32)
        por(tela, mesa, C @ mesa_M)
        # objetos fixos da mesa
        por(tela, filme_t, C @ mat_obj(330, 230, 0.55, -14, filme_t.shape[1], filme_t.shape[0]), sombra=1)
        por(tela, lupa, C @ mat_obj(1680, 880, 0.42, 28, lupa.shape[1], lupa.shape[0]), sombra=1, z=0.15)
        # a pasta chega deslizando (0.15–1.0 s)
        u = eout(lin(t, 0.15, 0.85)); px = FX + (1 - u) * 260; py = FY + (1 - u) * 760; pa = -14 * (1 - u)
        if t < 3.05:
            n = int(np.clip((t - 1.45) / 1.35 * tt, 0, tt))
            por(tela, fechada_com(n), C @ mat_obj(px, py, esc_f, pa, fechada0.width, fechada0.height), sombra=1, z=0.6 * (1 - u))
            if q == int(LENTO * 0.15 * FPS): sons.append((0.12, "ep09_papel", -6))
            if q == int(LENTO * 0.98 * FPS): sons.append((0.98, "impacto", -16))
            if 1.45 <= t < 2.8 and n > int(np.clip((t - 1.45 - 1 / FPS) / 1.35 * tt, 0, tt)): sons.append((t, "tecla", -9))
        else:
            # abre: a capa gira em 3D na lombada (0 → 180°, ~0,8 s), pousa e assenta; o verso vira a página da esquerda
            teta = 180 * ease(lin(t, 3.2, 0.85)) - 7 * math.sin(math.pi * lin(t, 4.05, 0.32))
            por(tela, pag_dir, C @ mat_obj(espinha + wf / 2, FY, esc_f, 0, fechada0.width, fechada0.height), sombra=1)
            if teta >= 179.9 or t > 4.4:
                por(tela, pag_esq, C @ mat_obj(espinha - wf / 2, FY, esc_f, 0, fechada0.width, fechada0.height), sombra=1)
            else:
                virar(tela, C, teta, fechada_com(tt), pag_esq, espinha, FY, wf, hf, (cx, cy))
            if q == int(LENTO * 3.2 * FPS): sons.append((3.2, "ep09_papel", -5))
            if q == int(LENTO * 4.03 * FPS): sons.append((4.03, "impacto", -22))
            # as provas saem da pasta e se espalham
            for (img, alvo, t0, som) in ((polA, PA, tA, "ep10_obturador"), (jornal, PJ, tJ, "ep09_papel"), (polB, PB, tB, "ep10_obturador")):
                w2 = eout(lin(t, t0, 0.7))
                if w2 <= 0: continue
                x = AX + (alvo[0] - AX) * w2; y = FY + 40 + (alvo[1] - FY - 40) * w2
                ang = alvo[3] + (1 - w2) * 25
                por(tela, img, C @ mat_obj(x, y, alvo[2] * (0.85 + 0.15 * w2), ang, img.shape[1], img.shape[0]), sombra=1, z=0.5 * (1 - w2) + 0.05)
                if q == int(LENTO * t0 * FPS): sons.append((t0, som, -12))
            # tachinhas caem
            for k, (x, y) in enumerate(pinos):
                t0 = 5.6 + k * 0.2; w3 = lin(t, t0, 0.18)
                if w3 <= 0: continue
                e = 0.11 * (1 + 1.4 * (1 - w3))
                por(tela, pino, C @ mat_obj(x, y, e, 0, pino.shape[1], pino.shape[0]), alfa=min(1, w3 * 3), sombra=1, z=0.6 * (1 - w3) + 0.1)
                if q == int(LENTO * (t0 + 0.17) * FPS): sons.append((t0 + 0.17, "ep11_lanterna_clique", -10))
            # a linha vermelha corre entre as pistas
            if t > 6.0:
                fio(tela, pinos, ease(lin(t, 6.0, 0.7)), C)
                if q == int(LENTO * 6.0 * FPS): sons.append((6.0, "ep09_sn_horror_whoosh", -18))
            # o carimbo: desce, bate (7.0 s), sobe e sai; a tinta fica
            if t >= 7.0:
                TX, TY = AX + 10, FY + 200
                Mt = C @ mat_obj(TX, TY, 0.57, -3, tinta.shape[1], tinta.shape[0])
                a = cv2.warpAffine(tinta, Mt[:2], (W, H)) * min(1, (t - 7.0) * 12)
                tela[:] = tela * (1 - a[..., None] * (1 - TINTA))
            if 6.45 <= t < 7.9:
                if t < 7.0: s = 1 - ein(lin(t, 6.45, 0.55)); zc = 1.6 * s
                else: s = ein(lin(t, 7.15, 0.75)); zc = 1.6 * s
                ex = AX + 10 + (s * 700 if t >= 7.0 else s * 260); ey = FY + 200 - (s * 520 if t >= 7.0 else s * 380)
                por(tela, carimbo, C @ mat_obj(ex, ey - 250 * 0.6, 0.6 * (1 + 0.35 * zc), -4, carimbo.shape[1], carimbo.shape[0]),
                    sombra=1, z=0.2 + zc)
            if q == int(LENTO * 6.45 * FPS): sons.append((6.4, "riser_tensao", -14))
            if q == int(LENTO * 7.0 * FPS): sons += [(6.98, "ep08_carimbo", -2), (6.98, "impacto", -6), (6.98, "braam_horror", -11)]
            # a ficha do episódio entra e é datilografada
            if t >= 7.95:
                w4 = eout(lin(t, 7.95, 0.6)); n = int(np.clip((t - 8.45) / 1.25 * tf, 0, tf))
                fi = ficha_com(n)
                por(tela, fi, C @ mat_obj(400 - (1 - w4) * 600, 245 - (1 - w4) * 200, 410 / fi.shape[1], -4, fi.shape[1], fi.shape[0]), sombra=1, z=0.3 * (1 - w4))
                if q == int(LENTO * 7.95 * FPS): sons.append((7.95, "ep09_papel", -8))
                if 8.45 <= t < 9.75 and n > int(np.clip((t - 8.45 - 1 / FPS) / 1.25 * tf, 0, tf)): sons.append((t, "tecla", -11))
        L = luz(t, cx, cy, z, rot)
        quadro = acabamento(tela, L, t, DUR)
        if so is not None:
            cv2.imwrite(f"/tmp/claude-0/kul/prev_{t:05.2f}.jpg", quadro); continue
        proc.stdin.write(quadro.tobytes())
    proc.stdin.close(); proc.wait()
    if so is None:
        mixar(saida, [(t0 * LENTO, nome, db) for t0, nome, db in sons], DUR * LENTO)


def mixar(saida, sons, dur):
    sons = [(0.0, "drone_terror", -9), (0.0, "drone_tensao", -15)] + sons
    ent, filt = [], []
    for k, (t, nome, db) in enumerate(sons):
        ent += ["-i", str(SONS / f"{nome}.mp3")]
        cauda = 0.35 if nome == "tecla" else (dur if nome.startswith("drone") else 3.5)
        filt.append(f"[{k + 1}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{cauda},afade=t=out:st={max(0, cauda - 0.3)}:d=0.3,"
                    f"volume={db}dB,adelay={int(t * 1000)}:all=1[s{k}]")
    filt.append("".join(f"[s{k}]" for k in range(len(sons))) + f"amix=inputs={len(sons)}:normalize=0,afade=t=in:d=0.4,"
                f"afade=t=out:st={dur - 0.8}:d=0.8,atrim=0:{dur},alimiter=limit=0.9[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida) + ".v.mp4", *ent, "-filter_complex", ";".join(filt),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(saida)], check=True)
    Path(str(saida) + ".v.mp4").unlink()
    print("ok", saida)


PREVIA = None
if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3].startswith("previa="):
        PREVIA = sys.argv[3].split("=")[1].split(",")
    if sys.argv[1] == "abertura":
        abertura(sys.argv[2])
