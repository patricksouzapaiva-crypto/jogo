"""O QUE É A CRIATURA? — as peças do formato (21/11), com o mesmo motor da abertura (criatura.py): mesa e quadro de
cortiça das camadas do usuário, fichas datilografadas, lupa que amplia de verdade, marcas à mão, carimbo e fita.
Peças:
  pista      PISTA Nº n + a frase (a lupa passa por cima e amplia)
  teoria     TEORIA Nº n + o nome (a ficha é presa no quadro de cortiça)
  checklist  a ficha de uma teoria com as pistas e ✓/✗ desenhados um a um + o total
  placar     as teorias lado a lado no quadro, os pontos subindo
  veredito   o carimbo bate na teoria vencedora, as outras apagam, a frase do veredito
  spoiler    fitas de aviso cruzam a tela + "pule para mm:ss"
Uso: python3 pecas.py <peça> saida.mp4 [previa=t1,t2]   (os textos do episódio ficam em EP_OUTRA_MAMAE)"""
import math, subprocess, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import criatura as K
from criatura import W, H, FPS, ease, eout, ein, lin, carregar, de_pil, mat_cam, mat_obj, por, luz, acabamento, mixar, FONTES, CAM

ELITE = str(FONTES / "SpecialElite-Regular.ttf")
STENCIL = str(FONTES / "StardosStencil-Bold.ttf")
VERM = (150, 24, 28)        # RGB da tinta vermelha (texto)
PRETO = (30, 26, 24)

EP_OUTRA_MAMAE = {   # 21/11: roteiro v6 (7 pistas; placar 1 · 4 · 7 · 9)
    "pistas": ["ELA PEDE PERMISSÃO", "ELA VIRA QUEM VOCÊ AMA", "O CORPO NÃO OBEDECE", "UMA CASA CHEIA DE SEGREDOS",
               "O DESEJO DA MENINA ACONTECE", "ELA QUER SER HUMANA", "ELA QUER TROCAR DE LUGAR"],
    "teorias": ["O DUPLO", "O DEMÔNIO TRAPACEIRO", "UMA COISA CRIADA PELO DESEJO", "UMA FADA QUE TROCA PESSOAS"],   # 22/11: a fada por último
    "itens": ["permissão", "vira quem ama", "corpo que muda", "casa com segredos", "desejo", "quer ser humana",
              "trocar de lugar"],
    "provas_final": ["o outro lado", "o \"não\" a derrota"],
    # marcas de cada teoria nas 7 pistas (roteiro: fada 7, duplo 1, demônio 4, tulpa 6)
    "checklists": [("O DUPLO", [0, 1, 0, 0, 0, 0, 0]), ("O DEMÔNIO", [1, 1, 1, 0, 1, 0, 0]),
                   ("A TULPA", [1, 1, 1, 1, 1, 1, 0]), ("A FADA QUE TROCA", [1, 1, 1, 1, 1, 1, 1])],
    "placar": [("O DUPLO", 1), ("DEMÔNIO TRAPACEIRO", 4), ("TULPA", 7), ("FADA TROCADORA", 9)],
    "total": 9, "vencedor": 3,
    "veredito": "A OUTRA MAMÃE É UMA FADA TROCADORA",
}


class Sons:
    def __init__(self): self.lista, self.feitos = [], set()
    def __call__(self, t, t0, nome, db):
        if t >= t0 and (t0, nome) not in self.feitos:
            self.feitos.add((t0, nome)); self.lista.append((t0, nome, db))


def renderizar(saida, dur, quadro, sons):
    so = [int(float(x) * FPS) for x in K.PREVIA] if K.PREVIA else None
    proc = None if so is not None else subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-pix_fmt", "yuv420p", str(saida) + ".v.mp4"], stdin=subprocess.PIPE)
    for q in range(int(dur * FPS)):
        t = q / FPS
        if so is not None and q not in so:
            continue
        tela, (cx, cy, z, rot) = quadro(t)
        img = acabamento(tela, luz(t, cx, cy, z, rot), t, dur)
        if so is not None:
            cv2.imwrite(f"/tmp/claude-0/kul/prev_{t:05.2f}.jpg", img); continue
        proc.stdin.write(img.tobytes())
    if proc:
        proc.stdin.close(); proc.wait(); mixar(saida, sons.lista, dur)


# ------------------------------------------------------------------ peças de texto
def fonte_que_cabe(txt, arq, tam, larg):
    while tam > 10 and ImageFont.truetype(arq, tam).getbbox(txt)[2] > larg:
        tam -= 2
    return ImageFont.truetype(arq, tam)


def quebrar(txt, arq, tam, larg):
    f = ImageFont.truetype(arq, tam); linhas, atual = [], ""
    for p in txt.split():
        if atual and f.getbbox(atual + " " + p)[2] > larg:
            linhas.append(atual); atual = p
        else:
            atual = (atual + " " + p).strip()
    return linhas + [atual]


class Ficha:
    """Ficha de arquivo com linhas datilografadas: cada linha = (texto, fonte, tamanho, cor, x, y) em fração da ficha.
    texto_ate(n) devolve a ficha com os n primeiros caracteres (na ordem das linhas)."""
    def __init__(self, linhas, base="ID07_ficha_2.png"):
        self.base = Image.open(CAM / base).convert("RGBA"); self.linhas = linhas; self.cache = {}
        self.total = sum(len(l[0]) for l in linhas)

    def texto_ate(self, n, extra=None):
        chave = (n, extra and extra[0])
        if chave not in self.cache:
            im = self.base.copy(); d = ImageDraw.Draw(im); resto = n
            for txt, arq, tam, cor, x, y in self.linhas:
                mostra = txt[:max(0, resto)]; resto -= len(txt)
                f = ImageFont.truetype(arq, tam)
                d.text((x * im.width, y * im.height), mostra, font=f, fill=cor + (240,))
            if extra:
                extra[1](im)
            self.cache[chave] = de_pil(im)
        return self.cache[chave]


def fundo(nome, M):
    img = carregar(nome)
    return img, mat_obj(960, 540, 2250 / img.shape[1], 0, img.shape[1], img.shape[0])


def lente(tela, C, cx, cy, r, zoom=1.45):
    """Amplia o que está debaixo do vidro da lupa (círculo de raio r, centro (cx, cy) no mundo)."""
    p = C @ np.array([cx, cy, 1], np.float32); rr = r * math.hypot(C[0, 0], C[1, 0])
    x0, y0 = int(p[0] - rr), int(p[1] - rr); x1, y1 = int(p[0] + rr), int(p[1] + rr)
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H:
        return
    S = np.array([[zoom, 0, (1 - zoom) * p[0]], [0, zoom, (1 - zoom) * p[1]]], np.float32)
    amp = cv2.warpAffine(tela, S, (W, H))
    yy, xx = np.ogrid[0:H, 0:W]
    m = np.clip((rr - np.sqrt((xx - p[0]) ** 2 + (yy - p[1]) ** 2)) / 3, 0, 1).astype(np.float32)
    brilho = np.clip(1 - np.sqrt((xx - p[0] + rr * 0.35) ** 2 + (yy - p[1] + rr * 0.35) ** 2) / (rr * 0.7), 0, 1) * 0.12
    tela[:] = tela * (1 - m[..., None]) + (amp * 1.06 + brilho[..., None]) * m[..., None]


def furo_da_lupa(img):
    """Centro e raio do vidro: o maior buraco transparente cercado pelo aro."""
    a = (img[..., 3] < 0.2).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(a)
    h, w = a.shape; melhor = None
    for k in range(1, n):
        x, y, ww, hh, ar = st[k]
        if x > 0 and y > 0 and x + ww < w and y + hh < h and (melhor is None or ar > st[melhor][4]):
            melhor = k
    x, y, ww, hh, _ = st[melhor]
    return (x + ww / 2, y + hh / 2), (ww + hh) / 4


def pista(saida, num, frase):
    """PISTA: a ficha entra na mesa, 'PISTA Nº n' em vermelho, a frase em preto, a lupa passa ampliando."""
    DUR = 6.6
    mesa, Mm = fundo("ID01_mesa_1.png", None)
    lupa = carregar("ID08_lupa_1.png"); (lcx, lcy), lr = furo_da_lupa(lupa)
    lupa_sem_vidro = lupa.copy(); yy, xx = np.ogrid[0:lupa.shape[0], 0:lupa.shape[1]]
    dentro = ((xx - lcx) ** 2 + (yy - lcy) ** 2) < (lr * 0.97) ** 2
    lupa_sem_vidro[dentro] = 0                                   # o vidro fica por conta da lente (texto ampliado)
    base = Image.open(CAM / "ID07_ficha_2.png"); larg = base.width * 0.86
    linhas = quebrar(frase, ELITE, 120, larg)
    tam = 120 if len(linhas) <= 2 else 96
    ls = [(f"PISTA Nº {num}", ELITE, 74, VERM, 0.07, 0.11)]
    for k, l in enumerate(linhas):
        ls.append((l, ELITE, tam, PRETO, 0.07, 0.36 + k * 0.2))
    fi = Ficha(ls); n1 = len(ls[0][0]); som = Sons(); esc = 1150 / fi.base.width; el = 0.62

    def quadro(t):
        z = 1.02 + 0.04 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0.6 - 0.6 * ease(lin(t, 0, 2)))
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        u = eout(lin(t, 0.1, 0.9)); som(t, 0.1, "ep09_papel", -6); som(t, 0.95, "impacto", -20)
        def nch(tt):
            return int(np.clip((tt - 1.15) / 0.7 * n1, 0, n1)) if tt < 1.9 else n1 + int(np.clip((tt - 2.05) / 1.6 * (fi.total - n1), 0, fi.total - n1))
        n = nch(t)
        if 1.15 < t < 3.7 and n > nch(t - 1 / FPS):
            som(t, round(t, 3), "tecla", -10)
        por(tela, fi.texto_ate(n), C @ mat_obj(960 + (1 - u) * 120, 560 + (1 - u) * 700, esc, -2 + (1 - u) * 9,
                                              fi.base.width, fi.base.height), sombra=1, z=0.5 * (1 - u))
        # a lupa atravessa a frase
        v = ease(lin(t, 3.9, 2.0))
        if t > 3.6:
            som(t, 3.75, "ep09_sn_horror_whoosh", -22)
            x = 1900 - v * 1400; y = 600 + math.sin(v * math.pi) * 40
            ent = eout(lin(t, 3.6, 0.5))
            Ml = mat_obj(x, y + (1 - ent) * 300, el, 20, lupa.shape[1], lupa.shape[0])
            gx, gy = (Ml @ np.array([lcx, lcy, 1], np.float32))[:2]
            if ent > 0.95:
                lente(tela, C, gx, gy, lr * el * 0.96)
            por(tela, lupa_sem_vidro, C @ Ml, alfa=ent, sombra=1, z=0.55)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def teoria(saida, num, nome):
    """TEORIA: a ficha cai no quadro de cortiça e é presa com uma tachinha; 'TEORIA Nº n' e o nome datilografados."""
    DUR = 5.8
    quad, Mq = fundo("ID02_quadro_1.png", None)
    pino_src = Image.open(CAM / "ID10_tachinhas_1.png").convert("RGBA")
    pino = de_pil(pino_src.crop((0, 0, int(pino_src.width / 3 * 0.95), pino_src.height)))
    base = Image.open(CAM / "ID07_ficha_2.png"); larg = base.width * 0.86
    linhas = quebrar(nome, ELITE, 118, larg); tam = 118 if len(linhas) <= 2 else 92
    ls = [(f"TEORIA Nº {num}", ELITE, 74, VERM, 0.07, 0.11)] + [(l, ELITE, tam, PRETO, 0.07, 0.36 + k * 0.2) for k, l in enumerate(linhas)]
    fi = Ficha(ls); n1 = len(ls[0][0]); som = Sons(); esc = 1150 / fi.base.width

    def quadro(t):
        z = 1.0 + 0.05 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, quad, C @ Mq)
        u = ein(lin(t, 0.15, 0.55)); s = 1 + 0.35 * (1 - u)          # cai em direção ao quadro
        som(t, 0.7, "impacto", -18)
        n = int(np.clip((t - 1.5) / 0.7 * n1, 0, n1)) if t < 2.2 else n1 + int(np.clip((t - 2.35) / 1.6 * (fi.total - n1), 0, fi.total - n1))
        nprev = int(np.clip((t - 1 / FPS - 1.5) / 0.7 * n1, 0, n1)) if t - 1 / FPS < 2.2 else n1 + int(np.clip((t - 1 / FPS - 2.35) / 1.6 * (fi.total - n1), 0, fi.total - n1))
        if 1.5 < t < 4.0 and n > nprev:
            som(t, round(t, 3), "tecla", -10)
        por(tela, fi.texto_ate(n), C @ mat_obj(960, 560, esc * s, -1.5, fi.base.width, fi.base.height), alfa=min(1, u * 3 + 0.01) if t > 0.15 else 0,
            sombra=1, z=0.9 * (1 - u) + 0.08)
        w3 = lin(t, 0.95, 0.2)
        if w3 > 0:
            por(tela, pino, C @ mat_obj(960, 560 - fi.base.height * esc * 0.43, 0.12 * (1 + 1.3 * (1 - w3)), 0, pino.shape[1], pino.shape[0]),
                alfa=min(1, w3 * 3), sombra=1, z=0.5 * (1 - w3) + 0.1)
            som(t, 1.12, "ep11_lanterna_clique", -8)
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def marca(d, x, y, tam, certo, prog):
    """✓ ou ✗ à mão, em vermelho, desenhado até 'prog' (0–1)."""
    cor = VERM + (235,) if certo else (60, 40, 36, 235)
    larg = max(4, int(tam * 0.13))
    if certo:
        pts = [(x, y + tam * 0.55), (x + tam * 0.35, y + tam * 0.9), (x + tam * 1.0, y + tam * 0.05)]
    else:
        pts = [(x, y + tam * 0.1), (x + tam * 0.85, y + tam * 0.95), None, (x + tam * 0.85, y + tam * 0.1), (x, y + tam * 0.95)]
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1) if pts[i] and pts[i + 1]]
    total = len(segs); feito = prog * total
    for k, (a, b) in enumerate(segs):
        f = min(1, max(0, feito - k))
        if f <= 0: break
        d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=cor, width=larg, joint="curve")


def checklist(saida, nome, itens, marcas, tempos=None, dur=None):
    """A ficha da teoria com as pistas: cada pista recebe ✓ ou ✗ à mão, uma por vez, e no fim o total.
    21/11: 2 colunas com quantas linhas precisar (até 9 itens); tempos = quando cada marca entra (senão 0,75 s cada)."""
    tempos = tempos or [3.2 + 0.75 * k for k in range(len(itens))]
    t_total = tempos[-1] + 0.75
    DUR = dur or t_total + 1.8
    quad, Mq = fundo("ID02_quadro_1.png", None)
    base = Image.open(CAM / "ID07_ficha_2.png")
    ls = [(nome, ELITE, 0, VERM, 0.07, 0.07)]
    ls[0] = (nome, ELITE, fonte_que_cabe(nome, ELITE, 84, base.width * 0.86).size, VERM, 0.07, 0.07)
    nl = -(-len(itens) // 2); passo = min(0.17, 0.48 / nl); tam = 60 if nl <= 3 else 50
    col = [(0.09 if k < nl else 0.55, 0.27 + (k % nl) * passo) for k in range(len(itens))]
    for k, it in enumerate(itens):
        ls.append((it, ELITE, tam, PRETO, col[k][0] + 0.07, col[k][1]))
    fi = Ficha(ls); som = Sons(); esc = 1250 / fi.base.width; total_txt = fi.total
    certos = sum(marcas)

    def desenhar_marcas(t):
        def f(im):
            d = ImageDraw.Draw(im)
            for k, ok in enumerate(marcas):
                p = lin(t, tempos[k], 0.35)
                if p > 0:
                    marca(d, col[k][0] * im.width, col[k][1] * im.height - 6, 70 if nl <= 3 else 58, ok, p)
            p = lin(t, t_total, 0.2)
            if p > 0:
                fz = ImageFont.truetype(STENCIL, 110)
                d.text((im.width * 0.62, im.height * 0.80 - 30), f"{certos} DE {len(itens)}", font=fz, fill=VERM + (int(240 * p),))
        return f

    def quadro(t):
        z = 1.0 + 0.04 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, quad, C @ Mq)
        u = eout(lin(t, 0.1, 0.8)); som(t, 0.1, "ep09_papel", -7)
        n = int(np.clip((t - 0.9) / 2.0 * total_txt, 0, total_txt))
        if 0.9 < t < 2.95 and int(t * 18) != int((t - 1 / FPS) * 18): som(t, round(t, 3), "tecla", -12)
        for k in range(len(itens)):
            som(t, tempos[k], "ep08_pincel", -8)
        som(t, t_total, "ep08_carimbo", -6)
        chave = (n, tuple(round(lin(t, x, 0.35), 1) for x in tempos + [t_total]))
        im = fi.texto_ate(n, (chave, desenhar_marcas(t)))
        por(tela, im, C @ mat_obj(960, 560 + (1 - u) * 700, esc, -1.2, fi.base.width, fi.base.height), sombra=1, z=0.4 * (1 - u))
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def cartoes_quadro(nomes, pontos, total):
    """As fichas pequenas das teorias, lado a lado, com os pontos (marcados em riscos de contagem)."""
    base = Image.open(CAM / "ID07_ficha_2.png"); fichas = []
    for nome in nomes:
        im = base.copy(); d = ImageDraw.Draw(im)
        linhas = quebrar(nome, ELITE, 130, im.width * 0.86)
        for k, l in enumerate(linhas):
            d.text((im.width * 0.07, im.height * (0.08 + 0.19 * k)), l, font=ImageFont.truetype(ELITE, 130), fill=PRETO + (240,))
        fichas.append(im)
    return fichas


def riscos(d, x, y, n, tam=70):
    """Riscos de contagem (IIII cortado a cada 5)."""
    for k in range(n):
        g, i = divmod(k, 5)
        x0 = x + g * tam * 1.6 + i * tam * 0.26
        if i < 4:
            d.line([(x0, y), (x0 + 4, y + tam)], fill=VERM + (235,), width=9)
        else:
            d.line([(x + g * tam * 1.6 - 14, y + tam * 0.75), (x + g * tam * 1.6 + tam * 1.05, y + tam * 0.2)], fill=VERM + (235,), width=9)


def placar(saida, placar_, total, vencedor=None, veredito=None):
    """PLACAR: as teorias lado a lado no quadro; os riscos sobem um a um. Com 'veredito': o carimbo bate na
    vencedora, as outras escurecem e a frase do veredito é datilografada numa tira de papel."""
    nomes = [p[0] for p in placar_]; pts = [p[1] for p in placar_]
    t_fim_pontos = 1.6 + max(pts) * 0.32
    DUR = t_fim_pontos + (5.2 if veredito else 1.8)
    quad, Mq = fundo("ID02_quadro_1.png", None)
    pino_src = Image.open(CAM / "ID10_tachinhas_1.png").convert("RGBA")
    pino = de_pil(pino_src.crop((0, 0, int(pino_src.width / 3 * 0.95), pino_src.height)))
    fichas = cartoes_quadro(nomes, pts, total); som = Sons()
    n = len(nomes); esc = 440 / fichas[0].width; xs = [960 + (k - (n - 1) / 2) * 460 for k in range(n)]; Y = 500
    tinta = K.tinta_carimbo(["CASO ENCERRADO", "VEREDITO"]) if veredito else None
    tira = None
    if veredito:   # tira de papel: uma faixa da ficha, só com a frase
        fb = Image.open(CAM / "ID07_ficha_2.png").convert("RGBA"); fb = fb.crop((0, int(fb.height * 0.30), fb.width, int(fb.height * 0.62)))
        tam_t = fonte_que_cabe(veredito, ELITE, 120, fb.width * 0.92).size
        tira = Ficha([(veredito, ELITE, tam_t, PRETO, 0.04, 0.28)]); tira.base = fb; tira.cache = {}
    cache = {}

    def ficha_com(k, m, apaga):
        ch = (k, m, round(apaga, 2))
        if ch not in cache:
            im = fichas[k].copy(); d = ImageDraw.Draw(im)
            riscos(d, im.width * 0.08, im.height * 0.58, m, 170)
            d.text((im.width * 0.70, im.height * 0.46), str(m), font=ImageFont.truetype(STENCIL, 300), fill=VERM + (240,))
            a = de_pil(im)
            if apaga > 0:
                a[..., :3] *= 1 - 0.55 * apaga
            cache[ch] = a
        return cache[ch]

    def quadro(t):
        z = 1.0 + 0.03 * ease(lin(t, 0, DUR)); C = mat_cam(960, 540, z, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, quad, C @ Mq)
        tv = t_fim_pontos + 0.6
        for k in range(n):
            u = eout(lin(t, 0.15 + k * 0.18, 0.6)); som(t, 0.15 + k * 0.18, "ep09_papel", -12)
            m = min(pts[k], int(max(0, t - 1.4) / 0.32))
            if m >= 1: som(t, 1.4 + (m - 1) * 0.32 + 0.001 * k, "ep08_pincel", -14)
            apaga = ease(lin(t, tv, 0.5)) if (veredito and k != vencedor) else 0
            cresce = ease(lin(t, tv, 0.7)) if (veredito and k == vencedor) else 0
            x = xs[k] + (960 - xs[k]) * cresce; y = Y + (1 - u) * 600 - cresce * 90 + apaga * 60
            e = esc * (1 + 0.75 * cresce)
            por(tela, ficha_com(k, m, apaga), C @ mat_obj(x, y, e, (-2, 1.5, -1, 2)[k % 4], fichas[k].width, fichas[k].height),
                sombra=1, z=0.4 * (1 - u) + 0.25 * cresce)
            if u > 0.95:
                por(tela, pino, C @ mat_obj(x, y - fichas[k].height * e * 0.42, 0.09, 0, pino.shape[1], pino.shape[0]), sombra=1, z=0.1)
        if veredito:
            som(t, tv - 0.05, "riser_tensao", -14)
            if t >= tv + 0.55:
                Mt = C @ mat_obj(960, Y - 60, 0.6, -6, tinta.shape[1], tinta.shape[0])
                a = cv2.warpAffine(tinta, Mt[:2], (W, H)) * min(1, (t - tv - 0.55) * 12)
                tela[:] = tela * (1 - a[..., None] * (1 - K.TINTA))
                som(t, tv + 0.53, "ep08_carimbo", -2); som(t, tv + 0.53, "impacto", -6); som(t, tv + 0.53, "braam_horror", -12)
            tt = tv + 1.3
            if t >= tt:
                w = eout(lin(t, tt, 0.6)); nn = int(np.clip((t - tt - 0.6) / 1.8 * tira.total, 0, tira.total))
                if tt + 0.6 < t < tt + 2.4 and int(t * 16) != int((t - 1 / FPS) * 16): som(t, round(t, 3), "tecla", -11)
                im = tira.texto_ate(nn)
                por(tela, im, C @ mat_obj(960, 880 + (1 - w) * 300, 1380 / im.shape[1], -0.8, im.shape[1], im.shape[0], ancora=(0.5, 0.5)),
                    sombra=1, z=0.3 * (1 - w))
        return tela, (960, 540, z, 0)
    renderizar(saida, DUR, quadro, som)


def spoiler(saida, pular="10:40"):
    """SPOILER: duas fitas de aviso cruzam a tela sobre a mesa escurecida; a ficha avisa para onde pular."""
    DUR = 5.4
    mesa, Mm = fundo("ID01_mesa_1.png", None); som = Sons()
    # fita amarela e preta com "SPOILER", gerada aqui
    fw, fh = 2600, 150
    fita = Image.new("RGBA", (fw, fh), (232, 190, 40, 255)); d = ImageDraw.Draw(fita)
    for x in range(-fh, fw, 120):
        d.polygon([(x, 0), (x + 60, 0), (x + 60 + fh, fh), (x + fh, fh)], fill=(20, 18, 16, 255))
    f = ImageFont.truetype(STENCIL, 92)
    for x in range(40, fw, 520):
        w = d.textlength("SPOILER", font=f); d.rectangle((x - 20, 22, x + w + 20, fh - 22), fill=(232, 190, 40, 255))
        d.text((x, 20), "SPOILER", font=f, fill=(20, 18, 16, 255))
    a = np.asarray(fita).astype(np.float32); a[..., :3] *= 0.92 + 0.08 * np.random.default_rng(1).random((fh, fw, 1))
    fita = de_pil(Image.fromarray(a.astype(np.uint8)))
    fi = Ficha([("AINDA NÃO VIU O FILME?", ELITE, 84, VERM, 0.07, 0.12), (f"PULE PARA {pular}", ELITE, 130, PRETO, 0.07, 0.42)])

    def quadro(t):
        C = mat_cam(960, 540, 1.03, 0)
        tela = np.zeros((H, W, 3), np.float32); por(tela, mesa, C @ Mm)
        tela *= 1 - 0.35 * ease(lin(t, 0, 0.6))
        u = eout(lin(t, 0.2, 0.9)); n = int(np.clip((t - 1.2) / 1.6 * fi.total, 0, fi.total))
        if 1.2 < t < 2.85 and int(t * 16) != int((t - 1 / FPS) * 16): som(t, round(t, 3), "tecla", -11)
        por(tela, fi.texto_ate(n), C @ mat_obj(960, 540 + (1 - u) * 700, 1100 / fi.base.width, -1.5, fi.base.width, fi.base.height), sombra=1, z=0.4 * (1 - u))
        for k, (ang, t0, y) in enumerate(((-7, 0.25, 120), (6, 0.55, 975))):
            v = eout(lin(t, t0, 0.7)); som(t, t0, "ep09_sn_horror_whoosh", -14)
            x = 960 + (1 - v) * (2600 if k == 0 else -2600)
            por(tela, fita, C @ mat_obj(x, y, 1.0, ang, fita.shape[1], fita.shape[0]), sombra=1, z=0.25)
        som(t, 0.95, "impacto", -16)
        return tela, (960, 540, 1.03, 0)
    renderizar(saida, DUR, quadro, som)


if __name__ == "__main__":
    peca, saida = sys.argv[1], sys.argv[2]
    resto = [a for a in sys.argv[3:] if not a.startswith("previa=")]   # pecas.py pista saida.mp4 3 [previa=1,2]
    for a in sys.argv[3:]:
        if a.startswith("previa="):
            K.PREVIA = a.split("=")[1].split(",")
    E = EP_OUTRA_MAMAE
    n = int(resto[0]) if resto and resto[0].isdigit() else 1
    if peca == "pista": pista(saida, n, E["pistas"][n - 1])
    elif peca == "teoria": teoria(saida, n, E["teorias"][n - 1])
    elif peca == "checklist":
        nome, m = E["checklists"][n - 1]; checklist(saida, nome, E["itens"], [bool(x) for x in m])
    elif peca == "porque":   # o porquê do veredito: as 9 provas da fada, uma por vez, nos tempos dados (s)
        ts = [float(x) for x in resto[0].split(",")]
        checklist(saida, "A FADA QUE TROCA", E["itens"] + E["provas_final"], [True] * 9, ts, ts[-1] + 6)
    elif peca == "placar": placar(saida, E["placar"], E["total"])
    elif peca == "veredito": placar(saida, E["placar"], E["total"], E["vencedor"], E["veredito"])
    elif peca == "spoiler": spoiler(saida, resto[0] if resto else "10:40")
