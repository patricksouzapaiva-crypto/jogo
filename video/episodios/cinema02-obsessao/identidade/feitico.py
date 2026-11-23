"""O QUE É A CRIATURA? #2 — Obsessão: as peças com a identidade PRÓPRIA do episódio (23/11, usuário: "itens diferentes na
tela de apresentação, checklist etc., pra ter uma identidade própria"). Usa o motor do #1 (cinema01/identidade/criatura.py:
câmera, sombra, grão), trocando os objetos (veludo, chumbo, prego, frasco, lacre, galho de salgueiro, fio vermelho),
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
    carretel = carregar("ID42_carretel_linha_vermelha_1.png"); galho = carregar("ID39_galho_salgueiro_inteiro_1.png")

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
        Mg = mat_obj(1530, 850, 0.6, -20, galho.shape[1], galho.shape[0]); por(tela, galho, C @ Mg, sombra=1, z=0.03)
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
