"""O QUE É A CRIATURA? #2 — Obsessão: as peças com a identidade PRÓPRIA do episódio (23/11, usuário: "itens diferentes na
tela de apresentação, checklist etc., pra ter uma identidade própria"). Usa o motor do #1 (cinema01/identidade/criatura.py:
câmera, sombra, grão), trocando os objetos (veludo, chumbo, prego, boneco de pano, alfinete, lacre, galho de salgueiro, fio vermelho),
a luz (vela, em vez de luminária) e a letra (IM Fell, livro antigo, em vez da máquina de escrever).
Peças:
  pista      etiqueta de pergaminho no fio vermelho, presa por um alfinete; "PISTA I" + a frase escrita à pena
  checklist  tábua de chumbo: as pistas riscadas; ✓ = nó de fio vermelho; ✗ = risco fundo; "N DE 7"; DESCARTADA = um
             prego atravessa a tábua (opcional: modo "apresentacao" só com os ✓ e sem total, para o Ato I)
Uso: python3 feitico.py <peça> saida.mp4 [n] [previa=t1,t2]"""
import math, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
BASE1 = AQUI.parents[1] / "cinema01-outra-mamae" / "identidade"
sys.path.insert(0, str(BASE1))
import criatura as K  # noqa: E402
K.CAM = AQUI / "camadas"
from criatura import W, H, FPS, ease, eout, lin, de_pil, mat_cam, mat_obj, por, mixar, FONTES  # noqa: E402
CAM = K.CAM

FELL = str(FONTES / "IMFellEnglish-400.ttf")
FELL_I = str(FONTES / "IMFellEnglish-400-italic.ttf")
FELL_SC = str(FONTES / "IMFellEnglishSC-400.ttf")
TINTA = (52, 22, 16)          # tinta ferrugem-escura (RGB) para a pena
SANGUE = (150, 18, 22)        # vermelho do fio e dos títulos
FIO_BGR = np.array([0.08, 0.06, 0.62], np.float32)

EP = {
    "pistas": ["O desejo tem regras", "O galho precisa ser quebrado", "Ela não sossega", "Quem atrapalha, morre",
               "A Nikki de verdade ainda está lá", "Ele escolheu por ela", "Mais do que qualquer pessoa no mundo"],
    "itens": ["tem regras", "o galho quebrado", "não sossega", "quem atrapalha morre", "a Nikki está lá dentro",
              "escolheu por ela", "ao pé da letra"],
    # ✓ de cada suspeito (provisório até a legenda): gênio 5 · amarração 7 · dybbuk 6 · pata 4
    "suspeitos": [("O GÊNIO", [1, 0, 1, 1, 1, 0, 1]), ("A AMARRAÇÃO", [1, 1, 1, 1, 1, 1, 1]),
                  ("O DYBBUK", [0, 0, 1, 1, 1, 1, 1]), ("A PATA DO MACACO", [1, 1, 0, 1, 0, 0, 1])],
}
ROMANOS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
rng = np.random.default_rng(11)


def carregar(nome):
    return K.carregar(nome)


def fundo(nome, larg=2250):
    img = carregar(nome)
    return img, mat_obj(960, 540, larg / img.shape[1], 0, img.shape[1], img.shape[0])


# ------------------------------------------------------------------ luz de vela e acabamento (≠ luminária do #1)
def luz_vela(t, cx, cy, z, rot, foco=(980, 600)):
    M = mat_cam(cx, cy, z, rot)
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32) * 4
    inv = np.linalg.inv(M); wx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; wy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]
    dx = 25 * math.sin(t * 2.3) + 12 * math.sin(t * 5.1)          # a chama balança: a poça de luz anda um pouco
    d = ((wx - foco[0] - dx) / 820) ** 2 + ((wy - foco[1]) / 600) ** 2
    tremor = 1 + 0.06 * math.sin(t * 9.7) + 0.045 * math.sin(t * 23.3 + 1) + 0.03 * math.sin(t * 41.9 + 2)
    L = (0.72 + 0.75 * np.exp(-d * 1.2)) * tremor
    return cv2.resize(L.astype(np.float32), (W, H))


def acabar(tela, L, t, fim, fade=True):
    img = tela * L[..., None]
    img = img * np.array([0.86, 0.95, 1.12], np.float32) * 1.12         # mais quente e mais vermelho que o #1 (BGR)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.5 * np.clip(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.6)) ** 2 - 0.12, 0, 1)
    img = img * v[..., None]
    img += (rng.standard_normal((H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)) * 0.024
    f = lin(t, 0, 0.45) if not fade else min(lin(t, 0, 0.45), 1 - lin(t, fim - 0.5, 0.5))
    return (np.clip(img * f, 0, 1) * 255).astype(np.uint8)


class Sons:
    def __init__(self): self.lista, self.feitos = [], set()
    def __call__(self, t, t0, nome, db):
        if t >= t0 and (t0, nome) not in self.feitos:
            self.feitos.add((t0, nome)); self.lista.append((t0, nome, db))


PREVIA = None
CAUDA = 6.0     # como no #1 (23/11): sem escurecer no fim e com a câmera ainda andando; o montador lê <saida>.util


def renderizar(saida, dur, quadro, sons):
    import subprocess
    total = dur + CAUDA
    if PREVIA:
        for x in PREVIA:
            t = float(x); tela, cam = quadro(min(t, dur - 1 / FPS))
            img = acabar(tela, luz_vela(min(t, dur), *cam), t, 1e9, fade=False)
            cv2.imwrite(f"/tmp/claude-0/feitico_prev_{Path(saida).stem}_{t:05.2f}.jpg", img)
        return
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
                             str(saida) + ".v.mp4"], stdin=subprocess.PIPE)
    for q in range(int(total * FPS)):
        t = q / FPS
        tela, cam = quadro(min(t, dur - 1 / FPS))
        img = acabar(tela, luz_vela(min(t, dur), *cam), t, 1e9, fade=False)
        if t > dur:
            M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + 0.012 * (t - dur))
            img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        proc.stdin.write(img.tobytes())
    proc.stdin.close(); proc.wait(); mixar(saida, sons.lista, total)
    Path(str(saida) + ".util").write_text(f"{dur:.3f}\n")


# ------------------------------------------------------------------ desenho: fio, nó, risco, texto à pena, texto riscado
def fio(tela, pts, alfa=1.0, larg=5):
    """fio vermelho de lã: traço escuro + traço claro deslocado (volume)"""
    if len(pts) < 2:
        return
    p = np.array(pts, np.int32).reshape(-1, 1, 2)
    m = np.zeros((H, W), np.float32)
    cv2.polylines(m, [p], False, 1.0, larg, cv2.LINE_AA)
    hl = np.zeros((H, W), np.float32); cv2.polylines(hl, [p - np.array([1, 2])], False, 1.0, max(1, larg // 3), cv2.LINE_AA)
    m *= alfa; hl *= alfa
    tela[:] = tela * (1 - m[..., None]) + FIO_BGR * m[..., None]
    tela[:] = tela + np.array([0.10, 0.10, 0.25], np.float32) * hl[..., None] * 0.6


def catenaria(a, b, queda, n=40):
    (x0, y0), (x1, y1) = a, b
    return [(x0 + (x1 - x0) * s, y0 + (y1 - y0) * s + queda * 4 * s * (1 - s)) for s in np.linspace(0, 1, n)]


def cabe(txt, arq, tam, larg, minimo=40):
    """o maior tamanho (até 'tam') em que o texto cabe na largura 'larg' (px)"""
    while ImageFont.truetype(arq, tam).getlength(txt) > larg and tam > minimo:
        tam -= 2
    return tam


def conferir(linhas, im, margem=0.04):
    """23/11 (usuário: "AMARRAÇÃO está cortada — verifique em todos"): nenhuma linha pode passar da borda do papel/chumbo.
    Se passar, a renderização PARA, em vez de sair uma palavra cortada."""
    for txt, arq, tam, _, x, y in linhas:
        w = ImageFont.truetype(arq, tam).getlength(txt)
        if x * im.width < margem * im.width - 1 or x * im.width + w > (1 - margem) * im.width + 1:
            raise SystemExit(f"TEXTO CORTADO: '{txt}' ({tam}px) vai de {x * im.width:.0f} a {x * im.width + w:.0f}, papel {im.width}px")


def escrita_pena(im, linhas, prog):
    """linhas = [(texto, fonte, tam, cor, x, y)] (fração do papel); prog 0..1 revela da esquerda p/ a direita, linha a
    linha, como uma pena escrevendo (máscara com borda macia), com a tinta um pouco mais escura no traço novo."""
    conferir(linhas, im)
    camada = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(camada)
    caixas = []
    for txt, arq, tam, cor, x, y in linhas:
        f = ImageFont.truetype(arq, tam); X, Y = x * im.width, y * im.height
        d.text((X, Y), txt, font=f, fill=cor + (235,)); caixas.append(d.textbbox((X, Y), txt, font=f))
    tot = sum(b[2] - b[0] for b in caixas); falta = prog * tot
    mask = Image.new("L", im.size, 0); dm = ImageDraw.Draw(mask)
    for b in caixas:
        w = b[2] - b[0]
        if falta <= 0: break
        dm.rectangle([b[0] - 4, b[1] - 10, b[0] + min(w, falta), b[3] + 14], fill=255); falta -= w
    mask = mask.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(3))
    camada.putalpha(Image.fromarray((np.asarray(camada.getchannel("A")).astype(np.float32) * np.asarray(mask) / 255).astype(np.uint8)))
    out = im.copy(); out.alpha_composite(camada); return out


def risco_texto(im, linhas, prog, cor_sulco=(14, 14, 18), brilho=(240, 240, 245), grosso=2):
    """texto RISCADO no chumbo com um prego: sulco escuro + rebarba clara deslocada; prog revela como o de cima"""
    from PIL import ImageFilter
    if linhas and linhas[0][0] != "DESCARTADA":   # a DESCARTADA é girada e conferida à parte
        conferir(linhas, im, margem=0.05)
    sulco = Image.new("L", im.size, 0); d = ImageDraw.Draw(sulco); caixas = []
    for txt, arq, tam, _, x, y in linhas:
        f = ImageFont.truetype(arq, tam); X, Y = x * im.width, y * im.height
        d.text((X, Y), txt, font=f, fill=255, stroke_width=grosso, stroke_fill=255); caixas.append(d.textbbox((X, Y), txt, font=f))
    tot = sum(b[2] - b[0] for b in caixas); falta = prog * tot
    mask = Image.new("L", im.size, 0); dm = ImageDraw.Draw(mask)
    for b in caixas:
        w = b[2] - b[0]
        if falta <= 0: break
        dm.rectangle([b[0] - 4, b[1] - 10, b[0] + min(w, falta), b[3] + 14], fill=255); falta -= w
    a = (np.asarray(sulco).astype(np.float32) / 255) * (np.asarray(mask).astype(np.float32) / 255)
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) / 255
    rebarba = np.roll(np.roll(a, 2, 0), 2, 1) * (1 - a)
    arr = np.asarray(im).astype(np.float32)
    rgb = arr[..., :3]
    rgb = rgb * (1 - 0.9 * a[..., None]) + np.array(cor_sulco, np.float32) * 0.9 * a[..., None]
    rgb = rgb * (1 - 0.7 * rebarba[..., None]) + np.array(brilho, np.float32) * 0.7 * rebarba[..., None]
    arr[..., :3] = rgb
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def visto_fio(d, x, y, tam, prog):
    """✓ (23/11, usuário: "o chumbo está meio confuso"): um VISTO claro, feito de fio vermelho, com um nó na ponta"""
    if prog <= 0: return
    a, b, c = (x - tam * 0.42, y - tam * 0.02), (x - tam * 0.1, y + tam * 0.32), (x + tam * 0.48, y - tam * 0.42)
    pts = [a, b, c]; L1 = math.dist(a, b); L2 = math.dist(b, c); falta = prog * 1.2 * (L1 + L2)
    if falta < L1:
        pts = [a, (a[0] + (b[0] - a[0]) * falta / L1, a[1] + (b[1] - a[1]) * falta / L1)]
    elif falta < L1 + L2:
        e = (falta - L1) / L2; pts = [a, b, (b[0] + (c[0] - b[0]) * e, b[1] + (c[1] - b[1]) * e)]
    larg = max(5, tam // 6)
    d.line(pts, fill=(95, 8, 12, 255), width=larg + 4, joint="curve")
    d.line(pts, fill=SANGUE + (255,), width=larg, joint="curve")
    d.line([(p[0] - 1, p[1] - 2) for p in pts], fill=(225, 80, 80, 200), width=max(1, larg // 4))
    r = larg * 0.75
    d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=(120, 10, 14, 255))   # o nó


def x_fundo(d, x, y, tam, prog):
    """✗: um X riscado fundo no chumbo"""
    if prog <= 0: return
    larg = max(6, tam // 6)
    for k, (p0, p1) in enumerate((((x - tam * .38, y - tam * .38), (x + tam * .38, y + tam * .38)),
                                  ((x + tam * .38, y - tam * .38), (x - tam * .38, y + tam * .38)))):
        e = min(1, max(0, prog * 2 - k))
        if e <= 0: continue
        q = (p0[0] + (p1[0] - p0[0]) * e, p0[1] + (p1[1] - p0[1]) * e)
        d.line([p0, q], fill=(10, 10, 12, 255), width=larg)
        d.line([(p0[0] + 2, p0[1] + 2), (q[0] + 2, q[1] + 2)], fill=(225, 225, 230, 160), width=max(1, larg // 3))


def no_vermelho(d, x, y, tam, prog):
    """✓ = um nó de fio vermelho: duas voltas e as pontas (desenhado aos poucos)"""
    if prog <= 0: return
    pts = []
    for k in range(40):
        s = k / 39 * 2 * math.pi * 1.6
        pts.append((x + math.cos(s) * tam * 0.32 * (1 + 0.15 * math.sin(3 * s)), y + math.sin(s) * tam * 0.22))
    n = max(2, int(len(pts) * min(1, prog * 1.3)))
    d.line(pts[:n], fill=SANGUE + (255,), width=max(3, tam // 9), joint="curve")
    if prog > 0.75:
        e = (prog - 0.75) / 0.25
        d.line([(x + tam * 0.25, y + tam * 0.05), (x + tam * (0.25 + 0.4 * e), y + tam * (0.05 + 0.35 * e))], fill=SANGUE + (255,), width=max(3, tam // 10))
        d.line([(x - tam * 0.25, y + tam * 0.05), (x - tam * (0.25 + 0.3 * e), y + tam * (0.05 + 0.4 * e))], fill=SANGUE + (255,), width=max(3, tam // 10))


# ------------------------------------------------------------------ PISTA
def pista(saida, num, frase):
    """A etiqueta de pergaminho desce balançando no fio vermelho, o alfinete a prende na mesa de veludo, e a pena escreve
    'PISTA I' (versalete, vermelho) e a frase (itálico, tinta escura)."""
    DUR = 6.8
    mesa, Mm = fundo("ID31_mesa_feitico_1.png")
    base = Image.open(CAM / "ID36_etiqueta_pergaminho_1.png").convert("RGBA")
    alf = carregar("ID41_alfinete_cabeca_preta_2.png")
    from criatura import texto_img  # noqa
    larg = base.width * 0.84
    for tam in (150, 132, 116, 102):   # o maior tamanho que fecha em até 3 linhas (4 no último)
        f = ImageFont.truetype(FELL_I, tam)
        palavras, linhas_txt, atual = frase.split(), [], ""   # como está escrita (nomes próprios)
        for p in palavras:
            if atual and f.getlength(atual + " " + p) > larg:
                linhas_txt.append(atual); atual = p
            else:
                atual = (atual + " " + p).strip()
        linhas_txt.append(atual)
        if len(linhas_txt) <= 3:
            break
    def centro(txt, arq, t_):
        return (1 - ImageFont.truetype(arq, t_).getlength(txt) / base.width) / 2
    altura = (tam / base.height) * 1.08 * len(linhas_txt)
    y0 = 0.32 + (0.58 - altura) / 2          # o bloco da frase no meio da área livre
    ls = [(f"Pista {ROMANOS[num - 1]}", FELL_SC, 128, SANGUE, centro(f"Pista {ROMANOS[num - 1]}", FELL_SC, 128), 0.17)]
    for k, l in enumerate(linhas_txt):
        ls.append((l, FELL_I, tam, TINTA, centro(l, FELL_I, tam), y0 + k * (tam / base.height) * 1.08))
    cache = {}
    som = Sons(); esc = 700 / base.width
    carretel = carregar("ID42_carretel_linha_vermelha_1.png"); galho = carregar("ID45_galho_filme_1.png")

    def etiqueta(prog):
        k = round(prog, 2)
        if k not in cache:
            cache[k] = de_pil(escrita_pena(base, ls, k))
        return cache[k]

    def quadro(t):
        z = 1.02 + 0.035 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, -0.5 + 0.5 * ease(lin(t, 0, 2.5)))
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        desce = eout(lin(t, 0.0, 1.1)); som(t, 0.05, "ep09_papel", -8)
        balanco = math.sin(t * 4.2) * 7 * math.exp(-t * 1.3) if t > 0.6 else 0
        cx, cy = 960, 560 - (1 - desce) * 1000
        Me = mat_obj(cx, cy, esc, balanco, base.width, base.height)
        furo = Me @ np.array([base.width * 0.5, base.height * 0.08, 1], np.float32)
        # a mesa ao redor: o carretel (o fio sai dele até a etiqueta) e o galho de salgueiro
        Mc = mat_obj(300, 800, 0.36, -12, carretel.shape[1], carretel.shape[0]); por(tela, carretel, C @ Mc, sombra=1, z=0.05)
        Mg = mat_obj(1530, 880, 0.5, -20, galho.shape[1], galho.shape[0]); por(tela, galho, C @ Mg, sombra=1, z=0.03)
        ponta = Mc @ np.array([carretel.shape[1] * 0.62, carretel.shape[0] * 0.55, 1], np.float32)
        pts = catenaria(ponta[:2], furo[:2], 120 * desce + 40)
        fio(tela, [(C @ np.array([px, py, 1], np.float32))[:2] for px, py in pts], 1.0, 6)
        prog = ease(lin(t, 1.3, 3.4))
        if 1.3 < t < 4.7:
            som(t, 1.3, "ep08_pincel", -16)
        por(tela, etiqueta(prog), C @ Me, sombra=1, z=0.35 * (1 - desce) + 0.06)
        crava = eout(lin(t, 1.0, 0.35))
        if t > 0.9:
            som(t, 1.05, "impacto", -22)
            Ma = mat_obj(furo[0] + 150 - 90 * crava, furo[1] - 10, 0.55, -8, alf.shape[1], alf.shape[0])
            por(tela, alf, C @ Ma, alfa=lin(t, 0.9, 0.15), sombra=1, z=0.15)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


# ------------------------------------------------------------------ CHECKLIST (tábua de chumbo)
def checklist(saida, nome, marcas, apresentacao=False):
    """A tábua de chumbo sobre o veludo; o nome riscado; cada pista riscada com o seu ✓ (nó vermelho) ou ✗ (risco).
    apresentacao=True (Ato I): só os ✓, sem ✗, sem total, sem DESCARTADA. Senão: 'N DE 7' e o prego atravessa a tábua."""
    itens = EP["itens"]; n = len(itens)
    tempos = [2.6 + 0.8 * k for k in range(n)]
    t_tot = tempos[-1] + 0.9
    t_desc = t_tot + 1.0
    DUR = (t_tot + 1.2) if apresentacao else (t_desc + 2.4)
    if apresentacao:
        marcas = [1 if m else None for m in marcas]
    mesa, Mm = fundo("ID31_mesa_feitico_2.png")
    from PIL import ImageEnhance
    base = Image.open(CAM / "ID33_tabua_chumbo_1.png").convert("RGBA")
    a_ = base.getchannel("A"); base = ImageEnhance.Contrast(ImageEnhance.Brightness(base.convert("RGB")).enhance(1.3)).enhance(0.8).convert("RGBA")
    base.putalpha(a_)   # chumbo mais claro e mais liso: o sulco escuro aparece
    prego = carregar("ID34_prego_ferro_1.png")
    t_tit = cabe(nome, FELL_SC, 104, base.width * 0.8)
    titulo = [(nome, FELL_SC, t_tit, None, 0.09, 0.06)]
    tam_l = 72   # o maior tamanho em que a linha mais longa cabe na tábua (de 0.235 até 0.93 da largura)
    while max(ImageFont.truetype(FELL, tam_l).getlength(it) for it in itens) > base.width * 0.69 and tam_l > 50:
        tam_l -= 2
    linhas = [(it, FELL, tam_l, None, 0.235, 0.215 + k * 0.093) for k, it in enumerate(itens)]
    som = Sons(); esc = 880 / base.height
    cache = {}

    def tabua(t):
        p_tit = ease(lin(t, 0.9, 1.0))
        ps = [ease(lin(t, tempos[k] - 0.55, 0.5)) for k in range(n)]
        pm = [lin(t, tempos[k], 0.45) for k in range(n)]
        p_tot = lin(t, t_tot, 0.5) if not apresentacao else 0
        p_desc = ease(lin(t, t_desc + 0.05, 0.6)) if not apresentacao else 0
        chave = (round(p_tit, 2), tuple(round(x, 2) for x in ps), tuple(round(x, 2) for x in pm), round(p_tot, 2), round(p_desc, 2))
        if chave not in cache:
            im = risco_texto(base, titulo, p_tit)
            im = risco_texto(im, linhas, sum(ps) / n if all(x >= 1 for x in ps[:-1]) or True else 0) if False else im
            for k in range(n):   # cada linha riscada no seu tempo
                im = risco_texto(im, [linhas[k]], ps[k])
            d = ImageDraw.Draw(im)
            for k, m in enumerate(marcas):
                if m is None: continue
                x, y = base.width * 0.135, base.height * (0.215 + k * 0.093) + 44
                if m:
                    visto_fio(d, x, y, 80, pm[k])
                else:
                    x_fundo(d, x, y, 62, pm[k])
            if p_tot > 0:
                im = risco_texto(im, [(f"{sum(1 for m in marcas if m)} DE {n}", FELL_SC, 110, None, 0.5, 0.86)], p_tot,
                                 cor_sulco=(150, 14, 18), brilho=(255, 190, 180))
            if p_desc > 0:   # DESCARTADA riscada fundo, em diagonal, em vermelho
                cam = Image.new("RGBA", im.size, (0, 0, 0, 0))
                cam = risco_texto(cam.convert("RGBA"), [("DESCARTADA", FELL_SC, 100, None, 0.1, 0.44)], p_desc,
                                  cor_sulco=(170, 14, 20), brilho=(255, 200, 190))
                a = np.asarray(risco_texto(Image.new("RGBA", im.size, (255, 255, 255, 255)),
                                           [("DESCARTADA", FELL_SC, 100, None, 0.1, 0.44)], p_desc)).astype(np.float32)
                m = Image.fromarray((np.clip((255 - a[..., 0]) * 1.6, 0, 255)).astype(np.uint8)).rotate(-18, resample=Image.BICUBIC, center=(im.width / 2, im.height / 2))
                verm = Image.new("RGBA", im.size, (168, 16, 22, 255)); verm.putalpha(m)
                im.alpha_composite(verm)
            cache[chave] = de_pil(im)
        return cache[chave]

    def quadro(t):
        z = 1.0 + 0.04 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        u = eout(lin(t, 0.1, 0.8)); som(t, 0.15, "impacto", -16)
        for k in range(n):
            som(t, tempos[k] - 0.55, "ep09_papel", -20)
        Mt = mat_obj(960, 545 + (1 - u) * 700, esc, -1.5, base.width, base.height)
        por(tela, tabua(t), C @ Mt, sombra=1, z=0.3 * (1 - u) + 0.05)
        if not apresentacao and t > t_desc - 0.4:   # o prego atravessa a tábua: DESCARTADA
            p = eout(lin(t, t_desc - 0.4, 0.35)); som(t, t_desc - 0.1, "impacto", -6)
            # crava no furinho do canto de cima à esquerda da tábua, vindo de fora: não cobre nenhum texto
            furo = Mt @ np.array([base.width * 0.035, base.height * 0.035, 1], np.float32)
            Lp = prego.shape[1] * 0.5
            ang = 35; dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            ponta = (furo[0] - (1 - p) * 220 * dx, furo[1] - (1 - p) * 220 * dy)
            Mp = mat_obj(ponta[0] - dx * Lp * 0.42, ponta[1] - dy * Lp * 0.42, 0.5, ang, prego.shape[1], prego.shape[0])
            por(tela, prego, C @ Mp, sombra=1, z=0.4 * (1 - p) + 0.05)
            if p >= 1:   # a palavra riscada em vermelho
                pass
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


# ------------------------------------------------------------------ bonecos de pano (TEORIA, PLACAR, VEREDITO)
# 23/11 (usuário: "não gostei desses frascos, vamos mudar pra outra coisa" → escolheu bonecos de pano): os 'poppets' sem
# rosto das amarrações inglesas. Cada pista que a teoria explica = um ALFINETE espetado no boneco; o descartado SE DESFAZ.
BONECO = [("ID43_boneco_1.png", "ID44_boneco_desfeito_1.png"), ("ID43_boneco_2.png", "ID44_boneco_desfeito_2.png")]
CINTURA = 0.52    # a faixa de fio vermelho no boneco (fração da altura)
# onde cada alfinete entra (fração do boneco) e para que lado fica a cabeça dele (graus)
FUROS = [(0.50, 0.16, 215), (0.27, 0.40, 160), (0.73, 0.41, 20), (0.47, 0.66, 185), (0.38, 0.82, 150), (0.63, 0.80, 30),
         (0.56, 0.30, -30)]


def pontos(marcas):
    return sum(1 for m in marcas if m)


def boneco_img(k):
    """(inteiro, desfeito) do suspeito k (linho e juta alternados)"""
    a, b = BONECO[k % 2]
    return carregar(a), carregar(b)


_ALF = {}


def alfinete():
    """o alfinete cravado visto de cima: só a cabeça e o começo da haste (o resto entrou no pano); a ponta à direita"""
    if "a" not in _ALF:
        a = carregar("ID41_alfinete_cabeca_preta_2.png"); _ALF["a"] = np.ascontiguousarray(a[:, : int(a.shape[1] * 0.42)])
    return _ALF["a"]


def cravar(tela, C, Mb, wh, furo, p, esc=0.30, alfa=1.0, solta=0.0):
    """um alfinete entrando no boneco (p 0..1: cai de cima e crava); solta 0..1: o alfinete sai voando (descarte)"""
    if p <= 0 or alfa <= 0: return
    a = alfinete(); fx, fy, ang = furo
    P = Mb @ np.array([fx * wh[0], fy * wh[1], 1], np.float32)
    e = eout(p)
    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    x = P[0] + dx * 120 * solta; y = P[1] + dy * 120 * solta - 60 * solta
    M = mat_obj(x, y, esc * (1.5 - 0.5 * e), ang + 180 + 40 * solta, a.shape[1], a.shape[0], ancora=(1.0, 0.5))
    por(tela, a, C @ M, alfa=alfa * min(1, p * 3) * (1 - solta), sombra=1, z=0.25 * (1 - e) + 0.03 + 0.3 * solta)


def etiqueta_nome(nome, sub=None, prog=1.0, risco=0.0, base_nome="ID36_etiqueta_pergaminho_1.png"):
    """a etiqueta de pergaminho com o nome do suspeito à pena (e 'SUSPEITO I' em vermelho em cima); risco 0..1 = um traço
    vermelho atravessando o nome (descartado)"""
    base = Image.open(CAM / base_nome).convert("RGBA")
    larg = base.width * 0.82
    linhas_txt = []
    for w_ in nome.split():   # uma palavra por linha, juntando os artigos curtos
        if linhas_txt and (len(linhas_txt[-1]) <= 2 or w_.lower() in ("do", "da", "de")):
            linhas_txt[-1] += " " + w_
        else:
            linhas_txt.append(w_)
    tam = min(cabe(l, FELL_SC, 150, larg) for l in linhas_txt)
    ls = []; yy = 0.24
    if sub:
        ts = cabe(sub, FELL_SC, 92, larg)
        ls.append((sub, FELL_SC, ts, SANGUE, (1 - ImageFont.truetype(FELL_SC, ts).getlength(sub) / base.width) / 2, yy))
        yy += ts * 1.25 / base.height
    bloco = len(linhas_txt) * tam * 1.08 / base.height
    yy += max(0, (0.88 - yy - bloco) / 2)
    for l in linhas_txt:
        ls.append((l, FELL_SC, tam, TINTA, (1 - ImageFont.truetype(FELL_SC, tam).getlength(l) / base.width) / 2, yy))
        yy += tam * 1.08 / base.height
    im = escrita_pena(base, ls, prog)
    if risco > 0:
        d = ImageDraw.Draw(im); x0, y0, x1, y1 = base.width * 0.1, base.height * 0.4, base.width * 0.9, base.height * 0.78
        d.line([(x0, y0), (x0 + (x1 - x0) * risco, y0 + (y1 - y0) * risco)], fill=SANGUE + (235,), width=22)
        arr = np.asarray(im).astype(np.float32); arr[..., :3] *= 1 - 0.3 * risco
        im = Image.fromarray(arr.astype(np.uint8), "RGBA")
    return im


def escurecer(img, f):
    out = img.copy(); out[..., :3] *= f; return out


def fio_em(tela, C, pts, larg=5, alfa=1.0):
    fio(tela, [(C @ np.array([x, y, 1], np.float32))[:2] for x, y in pts], alfa, larg)


def teoria(saida, num, nome):
    """TEORIA / SUSPEITO: o boneco de pano desliza para a mesa, a etiqueta chega amarrada a ele pelo fio vermelho e a pena
    escreve 'SUSPEITO I' + o nome."""
    DUR = 5.8
    mesa, Mm = fundo("ID31_mesa_feitico_1.png")
    carretel = carregar("ID42_carretel_linha_vermelha_2.png"); galho = carregar("ID45_galho_filme_1.png")
    bon, _ = boneco_img(num - 1); bh, bw = bon.shape[:2]; eb = 900 / bh
    et0 = Image.open(CAM / "ID36_etiqueta_pergaminho_1.png"); ew, eh = et0.size; ee = 760 / eh
    sub = f"SUSPEITO {ROMANOS[num - 1]}"
    cache = {}; som = Sons()

    def et(prog):
        k = round(prog, 2)
        if k not in cache:
            cache[k] = de_pil(etiqueta_nome(nome, sub, k))
        return cache[k]

    def quadro(t):
        z = 1.03 + 0.04 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0.4 - 0.4 * ease(lin(t, 0, 2)))
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        por(tela, carretel, C @ mat_obj(210, 930, 0.3, 10, carretel.shape[1], carretel.shape[0]), sombra=1, z=0.05)
        por(tela, galho, C @ mat_obj(1560, 105, 0.5, -6, galho.shape[1], galho.shape[0]), sombra=1, z=0.03)
        u = eout(lin(t, 0.0, 0.9)); som(t, 0.05, "ep09_papel", -14); som(t, 0.85, "impacto", -22)
        Mb = mat_obj(700 - (1 - u) * 1100, 560, eb, -4 + (1 - u) * 10, bw, bh); por(tela, bon, C @ Mb, sombra=1, z=0.1)
        v = eout(lin(t, 0.35, 0.8)); som(t, 0.4, "ep09_papel", -18)
        Me = mat_obj(1330 + (1 - v) * 900, 580, ee, 5 - (1 - v) * 8, ew, eh)
        a = Mb @ np.array([bw * 0.86, bh * CINTURA, 1], np.float32); b = Me @ np.array([ew * 0.5, eh * 0.09, 1], np.float32)
        pts = catenaria(a[:2], b[:2], 70)      # o fio passa por baixo da etiqueta e sai pelo furo (não risca o texto)
        fio_em(tela, C, pts[: max(2, int(len(pts) * ease(lin(t, 0.9, 0.5))))], 6)
        por(tela, et(ease(lin(t, 1.3, 2.6))), C @ Me, sombra=1, z=0.08)
        if t > 1.3: som(t, 1.3, "ep08_pincel", -18)
        if t > 1.4:   # a volta do fio no furo
            fio_em(tela, C, [tuple(b[:2] + np.array([-14 + 28 * s_, -8 * math.sin(s_ * math.pi)])) for s_ in np.linspace(0, 1, 8)], 6)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def placar(saida, nomes, marcas, descartados=()):
    """PLACAR: os 4 bonecos deitados lado a lado no veludo, cada um com a sua etiqueta; a cada rodada entra um alfinete
    em cada boneco que explica mais uma pista (sem número: conta-se pelos alfinetes). descartados = índices em ordem: os
    anteriores já aparecem desfeitos; o ÚLTIMO se desfaz agora (os alfinetes voam, o fio solta, o boneco desaba)."""
    DUR = 7.2
    mesa, Mm = fundo("ID31_mesa_feitico_2.png")
    n = len(nomes); xs = [300 + k * 440 for k in range(n)]
    bons = [boneco_img(k) for k in range(n)]
    ets = {}; som = Sons()
    pts_ = [pontos(m) for m in marcas]
    ja = set(descartados[:-1]); agora = descartados[-1] if descartados else None
    T_DESC = 4.7
    ew, eh = Image.open(CAM / "ID36_etiqueta_pergaminho_1.png").size; ee = 420 / eh

    def et(k, r):
        c = (k, round(r, 2))
        if c not in ets:
            nome = nomes[k].split(" ", 1)[1] if nomes[k].split(" ", 1)[0] in ("O", "A") else nomes[k]
            ets[c] = de_pil(etiqueta_nome(nome, None, 1.0, r))   # sem o artigo: cabe maior na etiqueta pequena
        return ets[c]

    def quadro(t):
        z = 1.0 + 0.03 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        for k in range(n):
            inteiro, desfeito = bons[k]; bh, bw = inteiro.shape[:2]; eb = 520 / bh
            entra = eout(lin(t, 0.15 + 0.2 * k, 0.6)); som(t, 0.15 + 0.2 * k, "ep09_papel", -20)
            if k in ja: d = 1.0
            elif k == agora: d = ease(lin(t, T_DESC, 0.8))
            else: d = 0.0
            treme = math.sin(t * 60) * 3 * (1 - d) * (lin(t, T_DESC - 0.4, 0.4) if k == agora else 0)
            Mb = mat_obj(xs[k] + treme, 365 - (1 - entra) * 800, eb, (-3, 2, -2, 3)[k % 4], bw, bh)
            por(tela, inteiro, C @ Mb, alfa=1 - d, sombra=1, z=0.08)
            if d > 0:
                dh, dw = desfeito.shape[:2]
                Md = mat_obj(xs[k], 370, 520 / dh * (1 + 0.04 * d), (-3, 2, -2, 3)[k % 4] + 4 * d, dw, dh)
                por(tela, escurecer(desfeito, 1 - 0.4 * d), C @ Md, alfa=d, sombra=1, z=0.04)
            if k == agora:
                som(t, T_DESC, "ep09_papel", -8); som(t, T_DESC + 0.05, "impacto", -14)
            for r in range(pts_[k]):   # os alfinetes (rodada r entra em todos que têm mais de r pontos)
                tr = 1.5 + 0.36 * r + 0.07 * k
                som(t, 1.5 + 0.36 * r, "impacto", -24)
                cravar(tela, C, Mb, (bw, bh), FUROS[r], lin(t, tr, 0.3), esc=0.24, alfa=0 if k in ja else 1,
                       solta=ease(lin(t, T_DESC + 0.04 * r, 0.5)) if k == agora else 0)
            Me = mat_obj(xs[k], 845 + (1 - entra) * 500, ee, (2, -3, 3, -2)[k % 4], ew, eh)
            por(tela, et(k, 1.0 if k in ja else (ease(lin(t, T_DESC + 0.5, 0.5)) if k == agora else 0)), C @ Me, sombra=1, z=0.05)
            a = Mb @ np.array([bw * 0.5, bh * 0.97, 1], np.float32); b = Me @ np.array([ew * 0.5, eh * 0.09, 1], np.float32)
            fio_em(tela, C, catenaria(a[:2], b[:2], 18), 4, alfa=1 - 0.6 * d)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def veredito(saida, num, frase):
    """VEREDITO: o boneco vencedor no centro; o fio vermelho dá voltas e o AMARRA inteiro; a cera cai no nó, o sinete
    desce e sela; uma tira de pergaminho embaixo recebe a frase do veredito à pena."""
    DUR = 10.0
    mesa, Mm = fundo("ID31_mesa_feitico_2.png")
    lacre = carregar("ID37_lacre_cera_vermelha_1.png"); sinete = carregar("ID38_sinete_latao_1.png")
    bon, _ = boneco_img(num - 1); bh, bw = bon.shape[:2]; eb = 700 / bh
    tira0 = Image.open(CAM / "ID36_etiqueta_pergaminho_2.png").convert("RGBA")
    tira0 = tira0.crop((0, int(tira0.height * 0.3), tira0.width, int(tira0.height * 0.62))).resize((1500, 260))
    tam = cabe(frase, FELL_I, 92, 1500 * 0.9)
    lt = [(frase, FELL_I, tam, TINTA, (1 - ImageFont.truetype(FELL_I, tam).getlength(frase) / 1500) / 2, 0.28)]
    cache = {}; som = Sons()
    # as voltas do fio: do peito até as pernas, de um lado ao outro do corpo (fração do boneco)
    voltas = []
    for q in range(321):
        s = q / 320; yv = 0.30 + 0.52 * s
        meia = 0.21 if yv < 0.6 else 0.27
        ang_ = s * 2 * math.pi * 5.5
        voltas.append((0.5 + meia * math.sin(ang_), yv + 0.02 * math.cos(ang_), math.cos(ang_) > 0))   # True = na frente

    def tira(prog):
        k = round(prog, 2)
        if k not in cache:
            cache[k] = de_pil(escrita_pena(tira0, lt, k))
        return cache[k]

    def quadro(t):
        z = 1.0 + 0.03 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        u = eout(lin(t, 0.0, 0.8)); som(t, 0.05, "ep09_papel", -14)
        Mb = mat_obj(960, 430 - (1 - u) * 900, eb, -2, bw, bh); por(tela, bon, C @ Mb, sombra=1, z=0.08)
        ev = ease(lin(t, 0.9, 2.0))
        if t > 0.9: som(t, 0.9, "whoosh", -20)
        if ev > 0:
            n_ = max(2, int(len(voltas) * ev)); trecho = []
            for q, (x, y, frente) in enumerate(voltas[:n_]):   # as voltas de trás aparecem pouco (passam atrás do pano)
                trecho.append(tuple((Mb @ np.array([x * bw, y * bh, 1], np.float32))[:2]))
                if q == n_ - 1 or voltas[q + 1][2] != frente:
                    fio_em(tela, C, trecho, 7 if frente else 4, alfa=1.0 if frente else 0.35); trecho = trecho[-1:]
        no = Mb @ np.array([bw * 0.5, bh * CINTURA, 1], np.float32)
        cai = ease(lin(t, 3.1, 0.5)); som(t, 3.1, "ep08_vela", -16)
        if t > 3.1:   # a cera cai e se espalha sobre o nó
            por(tela, lacre, C @ mat_obj(no[0], no[1], 0.09 + 0.07 * cai, 0, lacre.shape[1], lacre.shape[0]), alfa=min(1, cai * 2), sombra=1, z=0.02)
        desce = lin(t, 3.9, 0.6); sobe = lin(t, 4.9, 0.7)
        if 3.5 < t < 5.9:   # o sinete desce, aperta e sobe
            y = no[1] - 520 + 470 * ease(desce) - 600 * ease(sobe)
            som(t, 4.45, "ep08_carimbo", -6)
            por(tela, sinete, C @ mat_obj(no[0], y - 200, 0.42, 0, sinete.shape[1], sinete.shape[0]), sombra=1, z=0.4 * (1 - ease(desce)) + 0.05)
        v = eout(lin(t, 5.6, 0.8)); som(t, 5.6, "ep09_papel", -12)
        prog = ease(lin(t, 6.3, 2.6))
        if t > 6.3: som(t, 6.3, "ep08_pincel", -16)
        Mt = mat_obj(960, 955 + (1 - v) * 400, 0.92, -1, 1500, 260)
        por(tela, tira(prog), C @ Mt, sombra=1, z=0.1)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def spoiler(saida, pular):
    """SPOILER: a tábua de chumbo com 'SPOILER' riscado e 'pule para mm:ss'; dois fios vermelhos cruzam a tela e dão
    um nó no meio."""
    DUR = 6.0
    mesa, Mm = fundo("ID31_mesa_feitico_2.png")
    from PIL import ImageEnhance
    base = Image.open(CAM / "ID33_tabua_chumbo_2.png").convert("RGBA").rotate(90, expand=True)
    a_ = base.getchannel("A"); base = ImageEnhance.Contrast(ImageEnhance.Brightness(base.convert("RGB")).enhance(1.3)).enhance(0.8).convert("RGBA"); base.putalpha(a_)
    t1 = cabe("SPOILER", FELL_SC, 220, base.width * 0.8)
    l1 = [("SPOILER", FELL_SC, t1, None, (1 - ImageFont.truetype(FELL_SC, t1).getlength("SPOILER") / base.width) / 2, 0.16)]
    txt2 = f"pule para {pular}"; t2 = cabe(txt2, FELL_I, 110, base.width * 0.8)
    l2 = [(txt2, FELL_I, t2, None, (1 - ImageFont.truetype(FELL_I, t2).getlength(txt2) / base.width) / 2, 0.6)]
    cache = {}; som = Sons(); esc = 1250 / base.width

    def tabua(p1, p2):
        k = (round(p1, 2), round(p2, 2))
        if k not in cache:
            im = risco_texto(base, l1, p1, cor_sulco=(150, 14, 18), brilho=(255, 200, 190))
            cache[k] = de_pil(risco_texto(im, l2, p2))
        return cache[k]

    def quadro(t):
        z = 1.0 + 0.04 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        u = eout(lin(t, 0.0, 0.7)); som(t, 0.1, "impacto", -12)
        p1 = ease(lin(t, 0.7, 1.0)); p2 = ease(lin(t, 1.9, 1.2))
        if t > 0.7: som(t, 0.7, "ep09_papel", -16)
        por(tela, tabua(p1, p2), C @ mat_obj(960, 540 + (1 - u) * 600, esc, 1.5, base.width, base.height), sombra=1, z=0.05)
        f = ease(lin(t, 3.2, 1.0)); som(t, 3.2, "whoosh", -16)
        if f > 0:   # os dois fios cruzam e se encontram no centro
            for (ax, ay), (bx, by) in (((-100, 120), (2020, 960)), ((2020, 120), (-100, 960))):
                n = 40; pts = []
                for q in range(n + 1):
                    sq = q / n * f
                    pts.append((ax + (bx - ax) * sq, ay + (by - ay) * sq + 40 * math.sin(sq * math.pi)))
                fio(tela, [(C @ np.array([x, y, 1], np.float32))[:2] for x, y in pts], 1.0, 9)
        if f >= 1:   # o nó no meio
            no = np.zeros((H, W, 3), np.float32)
            cx, cy = (C @ np.array([960, 560, 1], np.float32))[:2]
            k = ease(lin(t, 4.2, 0.4)); som(t, 4.2, "ep06_estalo", -14)
            r = 34 * k
            cv2.circle(tela, (int(cx), int(cy)), int(r) + 1, tuple(float(v) for v in FIO_BGR * 0.7), -1, cv2.LINE_AA)
            cv2.ellipse(tela, (int(cx), int(cy)), (int(r * 1.3), int(r * 0.8)), 30, 0, 360, tuple(float(v) for v in FIO_BGR), 8, cv2.LINE_AA)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def abertura(saida, num="2", filme="OBSESSÃO"):
    """ABERTURA do arquivo (23/11, usuário: "não precisa da linha vermelha; o galho mais parecido com o do filme; vai ser
    só o galho quebrado no início"): o galho do filme sobre o veludo, ele treme e QUEBRA (estalo), as metades voam; o lacre
    de cera cai e o título aparece: O QUE É A CRIATURA? / arquivo nº 2 · Obsessão."""
    DUR = 8.6
    mesa, Mm = fundo("ID31_mesa_feitico_1.png")
    inteiro = carregar("ID45_galho_filme_1.png"); gh, gw = inteiro.shape[:2]
    qb = Image.open(CAM / "ID46_galho_filme_quebrado_1.png").convert("RGBA")
    a = np.asarray(qb.getchannel("A")).astype(np.float32).sum(0); m0 = int(qb.width * 0.4)
    corte = m0 + int(np.argmin(a[m0:int(qb.width * 0.6)]))          # a coluna vazia entre as duas metades
    meio1 = de_pil(qb.crop((0, 0, corte, qb.height))); meio2 = de_pil(qb.crop((corte, 0, qb.width, qb.height)))
    qh, qw = qb.height, qb.width
    lacre = Image.open(CAM / "ID37_lacre_cera_vermelha_2.png").convert("RGBA")
    lw = lacre.width
    tn = cabe(f"Nº {num}", FELL_SC, 340, lw * 0.5)
    tl = [(f"Nº {num}", FELL_SC, tn, None, (1 - ImageFont.truetype(FELL_SC, tn).getlength(f"Nº {num}") / lw) / 2, 0.30)]
    lacre_t = de_pil(risco_texto(lacre, tl, 1.0, cor_sulco=(70, 4, 8), brilho=(255, 140, 130)))
    tit = Image.new("RGBA", (1800, 520), (0, 0, 0, 0))
    som = Sons(); cache = {}

    def titulo(p1, p2):
        k = (round(p1, 2), round(p2, 2))
        if k not in cache:
            tt = cabe("O QUE É A CRIATURA?", FELL_SC, 150, 1800 * 0.88)
            ls = [("O QUE É A CRIATURA?", FELL_SC, tt, (236, 214, 190), (1 - ImageFont.truetype(FELL_SC, tt).getlength("O QUE É A CRIATURA?") / 1800) / 2, 0.05)]
            im = escrita_pena(tit, ls, p1)
            sub = f"arquivo nº {num} · {filme.lower().capitalize()}"
            ts = cabe(sub, FELL_I, 110, 1700)
            im = escrita_pena(im, [(sub, FELL_I, ts, (210, 60, 60), (1 - ImageFont.truetype(FELL_I, ts).getlength(sub) / 1800) / 2, 0.55)], p2)
            cache[k] = de_pil(im)
        return cache[k]

    def quadro(t):
        z = 1.1 - 0.08 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0.6 * math.sin(t * 0.4))
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        esc = 1.2; gx, gy = 960, 560
        quebra = 2.4
        if t < quebra:   # o galho sozinho; antes de quebrar ele treme cada vez mais
            tr = lin(t, 1.2, quebra - 1.2) ** 2
            som(t, 1.2, "ep09_sn_riser_cordas", -20)
            Mg = mat_obj(gx + math.sin(t * 70) * 4 * tr, gy, esc, -6 + math.sin(t * 53) * 0.8 * tr, gw, gh)
            por(tela, inteiro, C @ Mg, sombra=1, z=0.04)
        else:
            som(t, quebra, "ep11_galho_quebra", -4); som(t, quebra + 0.02, "ep06_estalo", -8)
            e = eout(lin(t, quebra, 0.5))
            x_q = gx - (qw / 2 - corte) * esc     # onde fica a quebra na tela
            M1 = mat_obj(x_q - 330 * e, gy - 150 * e, esc * (1 - 0.25 * e), -6 - 28 * e, corte, qh, ancora=(1.0, 0.5))
            M2 = mat_obj(x_q + 6 + 360 * e, gy - 170 * e, esc * (1 - 0.25 * e), -6 + 30 * e, qw - corte, qh, ancora=(0.0, 0.5))
            por(tela, meio1, C @ M1, sombra=1, z=0.04); por(tela, meio2, C @ M2, sombra=1, z=0.04)
            if t < quebra + 0.12:   # o tranco do estalo
                tela *= 1.25
        cai = eout(lin(t, 3.2, 0.45))
        if t > 3.0:
            som(t, 3.55, "impacto", -6)
            el = 0.42 * (1.6 - 0.6 * cai)
            por(tela, lacre_t, C @ mat_obj(960, 400, el, -4, lacre.width, lacre.height), alfa=min(1, lin(t, 3.0, 0.25)), sombra=1, z=0.5 * (1 - cai) + 0.05)
        p1 = ease(lin(t, 4.2, 1.4)); p2 = ease(lin(t, 5.4, 1.3))
        if t > 4.2:
            som(t, 4.2, "ep09_sn_gongo_cinema", -12)
            por(tela, titulo(p1, p2), mat_obj(960, 850, 1.0, 0, 1800, 520), sombra=0)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


if __name__ == "__main__":
    peca, saida = sys.argv[1], sys.argv[2]
    resto = [a for a in sys.argv[3:] if not a.startswith("previa=")]
    for a in sys.argv[3:]:
        if a.startswith("previa="):
            PREVIA = a.split("=")[1].split(",")
    nn = int(resto[0]) if resto and resto[0].isdigit() else 1
    if peca == "pista":
        pista(saida, nn, EP["pistas"][nn - 1])
    elif peca in ("checklist", "suspeito"):
        nome, m = EP["suspeitos"][nn - 1]
        checklist(saida, nome, [bool(x) for x in m], apresentacao=(peca == "suspeito"))
    elif peca == "teoria":
        teoria(saida, nn, EP["suspeitos"][nn - 1][0])
    elif peca == "placar":   # placar <saida> [desc1,desc2] : Ato I (iguais) ou julgamento (com descartados)
        desc = tuple(int(x) for x in resto[0].split(",")) if resto else ()   # ex.: 3 · 3,0 · 3,0,2
        placar(saida, [n_ for n_, _ in EP["suspeitos"]], [m for _, m in EP["suspeitos"]], desc)
    elif peca == "veredito":
        veredito(saida, 2, "Aquilo dentro da Nikki é uma amarração.")
    elif peca == "spoiler":
        spoiler(saida, resto[0] if resto else "14:20")
    elif peca == "abertura":
        abertura(saida)
