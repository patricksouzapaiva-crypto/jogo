"""Teste de estilo (28/11): ANALOG HORROR em fotomontagem, SEM imagem gerada por IA.
Matéria-prima: filmes caseiros em DOMÍNIO PÚBLICO do Prelinger Archives (archive.org):
  - "Home Movie: 002414" ('Way Down South in Dixie', cor) — campo, galpões, estrada no morro
  - "Home Movie: 97378: Maine" (1938, p&b) — lua entre as árvores, casa na neve, e o homem de chapéu (recortado
    por contraste: silhueta escura sobre a neve, sem ferramenta de IA)
Fotomontagem: quadro do filme → "noite americana" (escurece, esfria) → a figura recortada, esticada (alta demais),
na luz da cena → neblina em camadas que se movem → câmera lenta → cópia de 8 mm passada para VHS (cor vazando,
ruído, linhas de tracking, OSD). Cartões de texto à moda do gênero. Som todo sintetizado (chiado, zumbido, drone).
Uso: python3 montagem.py <pasta dos filmes pd> <saida.mp4>"""
import math, subprocess, sys, wave
from pathlib import Path
import cv2, numpy as np

PD = Path(sys.argv[1]); SAIDA = Path(sys.argv[2])
FPS, W, H = 30, 720, 540            # trabalha em 4:3 de VHS; no fim vai para 1440x1080 dentro de 1920x1080
rng = np.random.default_rng(7)
TMP = SAIDA.parent / "_quadros"; TMP.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTE_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def quadro(arquivo, t):
    o = TMP / f"src_{Path(arquivo).stem}_{t}.png"
    if not o.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(PD / arquivo), "-frames:v", "1", str(o)], check=True)
    return cv2.imread(str(o)).astype(np.float32) / 255


def limpar_bordas(im, l, r, t=0, b=0):
    """tira a borda da película/perfurações e volta a 4:3"""
    h, w = im.shape[:2]
    return cv2.resize(im[t:h - b, l:w - r], (W, H), interpolation=cv2.INTER_CUBIC)


def noite(im, exp=0.42, frio=(1.18, 1.0, 0.78), sat=0.45, ceu=0.5):
    """noite americana: escurece, esfria, tira cor; o céu (alto do quadro) desce mais"""
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[..., None]
    im = g + (im - g) * sat
    im = np.power(np.clip(im * exp, 0, 1), 1.25) * np.array(frio, np.float32)
    grad = np.linspace(ceu, 1.0, H, dtype=np.float32)[:, None, None]
    return np.clip(im * grad, 0, 1)


def pb(im, exp=1.0):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return np.clip(np.repeat(g[..., None], 3, 2) * exp * np.array([1.02, 1.0, 0.96], np.float32), 0, 1)


# ---------- a figura: homem de chapéu, recortado do filme de 1938 ----------
def figura():
    im = quadro("HMMaine97378.mp4", 317.5)
    g = cv2.cvtColor((im * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    x0, y0, x1, y1 = 395, 140, 520, 425
    c = g[y0:y1, x0:x1]
    m = (c < np.percentile(c, 30) + 8).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    m = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    tex = c[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) / 255
    h, w = m.shape   # alto demais e magro demais: 1,45× de altura, 0,8× de largura; pernas ainda mais longas
    alto = cv2.resize(m, (int(w * 0.8), int(h * 1.45)), interpolation=cv2.INTER_CUBIC)
    tex = cv2.resize(tex, (alto.shape[1], alto.shape[0]), interpolation=cv2.INTER_CUBIC)
    corte = int(alto.shape[0] * 0.62)
    pernas = cv2.resize(alto[corte:], (alto.shape[1], int((alto.shape[0] - corte) * 1.35)))
    tpern = cv2.resize(tex[corte:], (alto.shape[1], pernas.shape[0]))
    alfa = np.vstack([alto[:corte], pernas]).astype(np.float32) / 255
    tex = np.vstack([tex[:corte], tpern])
    alfa = cv2.GaussianBlur(alfa, (3, 3), 0.8)
    return alfa, tex


FIG_A, FIG_T = figura()


def por_figura(fundo, cx, base, altura, tom=0.04, borrar=0.0, luz_borda=0.0, opac=1.0):
    """põe a figura com os pés em (cx, base), com 'altura' px; o tom da silhueta é o escuro da cena"""
    a, t = FIG_A, FIG_T
    esc = altura / a.shape[0]
    a = cv2.resize(a, (max(2, int(a.shape[1] * esc)), int(altura)), interpolation=cv2.INTER_AREA)
    t = cv2.resize(t, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    if borrar:
        k = int(borrar) * 2 + 1; a = cv2.GaussianBlur(a, (k, k), borrar); t = cv2.GaussianBlur(t, (k, k), borrar)
    h, w = a.shape; x0, y0 = int(cx - w / 2), int(base - h)
    out = fundo.copy()
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya:
        return out
    aa = a[ya - y0:yb - y0, xa - x0:xb - x0, None] * opac
    cor_fundo = out[ya:yb, xa:xb]
    escuro = np.min(cv2.blur(fundo, (31, 31)).reshape(-1, 3), 0)          # o preto da própria cena
    sil = escuro * 0.35 + tom * 0.3 + t[ya - y0:yb - y0, xa - x0:xb - x0, None] * 0.05
    if luz_borda:   # contraluz fraca no contorno (lua/lâmpada atrás)
        ed = cv2.morphologyEx(a, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))[ya - y0:yb - y0, xa - x0:xb - x0, None]
        sil = sil + ed * luz_borda
    out[ya:yb, xa:xb] = cor_fundo * (1 - aa) + sil * aa
    sombra = np.zeros((H, W), np.float32)   # sombra no chão, deitada
    cv2.ellipse(sombra, (int(cx + w * 0.4), int(base)), (int(w * 0.9), max(2, int(w * 0.12))), 0, 0, 360, 0.35 * opac, -1)
    sombra = cv2.GaussianBlur(sombra, (0, 0), 3)[..., None]
    return out * (1 - sombra) + out * sombra * 0.4


# ---------- neblina em camadas ----------
def ruido_suave(w, h, escala, sem):
    r = np.random.default_rng(sem).random((max(2, h // escala), max(2, w // escala))).astype(np.float32)
    return cv2.GaussianBlur(cv2.resize(r, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), escala * 0.6)


NEB = [ruido_suave(W * 2, H, 60, 1), ruido_suave(W * 2, H, 25, 2)]


def neblina(im, t, chao=0.55, forca=0.35, cor=(0.55, 0.58, 0.62), vel=(6, 14)):
    out = im
    for k, (n, v) in enumerate(zip(NEB, vel)):
        dx = int(t * v) % W
        camada = n[:, dx:dx + W]
        mask = np.clip((np.linspace(0, 1, H)[:, None] - chao) / (1 - chao) * 1.6, 0, 1).astype(np.float32)
        mask = np.maximum(mask, 0.25 * (k == 0))
        a = np.clip((camada - 0.35) * 2.2, 0, 1) * mask * forca * (0.7 if k else 1.0)
        out = out * (1 - a[..., None]) + np.array(cor, np.float32) * a[..., None]
    return out


# ---------- câmera ----------
def camera(im, p, z0=1.0, z1=1.08, cx=(0.5, 0.5), cx1=None):
    cx1 = cx1 or cx
    z = z0 + (z1 - z0) * (0.5 - 0.5 * math.cos(math.pi * p))
    px = cx[0] + (cx1[0] - cx[0]) * p; py = cx[1] + (cx1[1] - cx[1]) * p
    M = np.float32([[z, 0, W / 2 - z * px * W], [0, z, H / 2 - z * py * H]])
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ---------- película de 8 mm ----------
POEIRA = [(rng.integers(0, W), rng.integers(0, H), rng.integers(1, 3)) for _ in range(400)]


def pelicula(im, f):
    dx, dy = rng.normal(0, 0.6), rng.normal(0, 0.8)              # tremor do projetor
    im = cv2.warpAffine(im, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    im = im * (1 + rng.normal(0, 0.025))                          # cintilação
    for _ in range(rng.poisson(1.5)):                             # poeira e fio de cabelo
        x, y, r = POEIRA[rng.integers(len(POEIRA))]
        cv2.circle(im, (int(x), int(y)), int(r), (0.02, 0.02, 0.02) if rng.random() < 0.7 else (0.8, 0.8, 0.78), -1)
    if rng.random() < 0.04:
        x = int(rng.integers(0, W)); cv2.line(im, (x, 0), (x + int(rng.integers(-20, 20)), H), (0.75, 0.75, 0.7), 1)
    vin = cv2.getGaussianKernel(H, H * 0.55) @ cv2.getGaussianKernel(W, W * 0.55).T
    return im * (0.55 + 0.45 * (vin / vin.max()))[..., None]


# ---------- VHS ----------
def vhs(im, f, rastro=0.0, osd=None):
    im = np.clip(im, 0, 1).astype(np.float32)
    y = cv2.cvtColor(im, cv2.COLOR_BGR2YCrCb)
    y[..., 1] = np.roll(cv2.blur(y[..., 1], (11, 1)), 3, 1)      # a cor vaza para o lado
    y[..., 2] = np.roll(cv2.blur(y[..., 2], (11, 1)), 3, 1)
    lum = y[..., 0]; y[..., 0] = np.clip(lum + (lum - cv2.blur(lum, (5, 1))) * 0.6, 0, 1)   # halo de nitidez
    im = cv2.cvtColor(y, cv2.COLOR_YCrCb2BGR)
    im = im + rng.normal(0, 0.028, (H, W, 1)).astype(np.float32)
    im[::2] *= 0.93                                                 # linhas
    if rastro > 0 or rng.random() < 0.03:                           # faixas de tracking
        n = int(3 + rastro * 10)
        for _ in range(n):
            yy = int(rng.integers(0, H)); hh = int(rng.integers(2, 6 + int(rastro * 20)))
            im[yy:yy + hh] = np.roll(im[yy:yy + hh], int(rng.integers(-40, 40) * (0.3 + rastro)), 1) + rng.normal(0.1, 0.15)
    base = im[H - 14:]
    im[H - 14:] = np.roll(base, int(rng.integers(-8, 8)), 1) + rng.normal(0, 0.12, base.shape)   # o pé da fita
    im = np.clip(im, 0, 1)
    if osd:
        img = (im * 255).astype(np.uint8)
        for txt, pos, tam in osd:
            cv2.putText(img, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, tam, (20, 20, 20), 4, cv2.LINE_AA)
            cv2.putText(img, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, tam, (235, 235, 235), 2, cv2.LINE_AA)
        im = img.astype(np.float32) / 255
    return im


def estatica(f):
    n = rng.random((H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_NEAREST)
    return np.repeat(n[..., None], 3, 2) * 0.85


# ---------- cartões de texto (PIL para acento) ----------
from PIL import Image, ImageDraw, ImageFont


def cartao(linhas, p, cor_fundo=(12, 14, 40), cor=(230, 230, 230), vermelho=None):
    img = Image.new("RGB", (W, H), cor_fundo); d = ImageDraw.Draw(img)
    fn = ImageFont.truetype(FONTE, 25); fb = ImageFont.truetype(FONTE_B, 29)
    total = sum(len(l) for l in linhas); mostrar = int(total * min(1, p * 1.6))   # digita
    y = H // 2 - len(linhas) * 21
    for l in linhas:
        txt = l[:max(0, mostrar)]; mostrar -= len(l)
        f = fb if l.isupper() else fn
        w = d.textlength(l, font=f)
        d.text(((W - w) / 2, y), txt, font=f, fill=vermelho if (vermelho and l == linhas[-1]) else cor)
        y += 42
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR).astype(np.float32) / 255


# ---------- as placas (fotomontagens) ----------
A = noite(limpar_bordas(quadro("206224_Home_Movie_002414.mp4", 82), 64, 64, 48, 66), exp=0.62, ceu=0.5)
B = noite(limpar_bordas(quadro("206224_Home_Movie_002414.mp4", 134), 64, 64, 48, 66), exp=0.62, ceu=0.55)
C = noite(limpar_bordas(quadro("206224_Home_Movie_002414.mp4", 160), 64, 64, 48, 66), exp=0.58, ceu=0.5)
D = pb(limpar_bordas(quadro("HMMaine97378.mp4", 834), 4, 4), 0.95)
E = pb(limpar_bordas(quadro("HMMaine97378.mp4", 820), 4, 4), 0.55)

# figura em cada placa: (cx, pés, altura) — cada vez mais perto
A1 = por_figura(A, 560, 372, 52, borrar=0.6)
B1 = por_figura(B, 590, 430, 132, borrar=0.4)
C1 = por_figura(C, 455, 470, 250, borrar=0.3)
C2 = por_figura(C, 380, 540, 470, borrar=0.2)            # o "salto": 4 quadros só
E1 = por_figura(E, 520, 330, 205, tom=0.02, luz_borda=0.10)

# janela acesa na casa (a casa está acordada)
def janela(im, x, y, w, h, f):
    out = im.copy(); a = 0.55 + 0.1 * math.sin(f * 0.9) + rng.normal(0, 0.03)
    cv2.rectangle(out, (x, y), (x + w, y + h), (0.55 * a, 0.75 * a, 0.95 * a), -1)
    return cv2.addWeighted(out, 1, cv2.GaussianBlur(out - im, (0, 0), 9), 0.8, 0)

SEG = [  # (nome, duração s)
    ("c1", 7.0), ("tA", 0.8), ("A", 8.0), ("tB", 0.7), ("B", 7.5), ("tC", 0.7), ("C", 8.0), ("t2", 0.9),
    ("c2", 6.0), ("tD", 0.8), ("D", 6.0), ("tE", 0.7), ("E", 8.5), ("tF", 1.2), ("c3", 7.0), ("fim", 2.0)]
CONT = {"A": "0:12:41", "B": "0:12:58", "C": "0:13:20", "D": "0:15:02", "E": "0:15:31"}


def render():
    f = 0; t0 = 0.0; marcas = []
    for nome, dur in SEG:
        n = int(round(dur * FPS)); marcas.append((nome, t0, dur))
        for i in range(n):
            p = i / max(1, n - 1); t = t0 + i / FPS
            osd = None
            if nome == "c1":
                im = cartao(["ARQUIVO DA FAMÍLIA WILLARD", "rolos de 8 mm transferidos para VHS em 1994",
                             "ROLO 3 DE 7"], p)
                im = vhs(im, f)
            elif nome == "c2":
                im = vhs(cartao(["Ninguém da família sabe dizer", "quem filmou este rolo.",
                                 "", "O PAI ESTÁ EM TODAS AS CENAS."], p), f)
            elif nome == "c3":
                im = vhs(cartao(["Se você reconhecer o homem de chapéu,", "não diga o nome dele em voz alta.", "",
                                 "ELE SÓ ATRAVESSA PORTAS ABERTAS."], p, cor_fundo=(8, 8, 10), vermelho=(200, 40, 40)), f,
                         rastro=0.4 if p > 0.92 else 0.0)
            elif nome == "fim":
                im = vhs(np.full((H, W, 3), (0.05, 0.05, 0.2), np.float32) * (1 - p), f)
            elif nome.startswith("t"):   # troca: a fita "rola" — estática e tracking por cima da imagem que some
                im = vhs(estatica(f) * (0.4 + 0.6 * math.sin(math.pi * p)), f, rastro=1.0)
            else:
                pl = {"A": A1, "B": B1, "C": C1, "D": D, "E": E1}[nome]
                if nome == "C" and 0.62 < p < 0.62 + 4 / n:
                    pl = C2
                if nome == "E":
                    pl = janela(pl, 566, 196, 16, 11, f)
                cam = {"A": dict(z1=1.10, cx=(0.5, 0.5), cx1=(0.62, 0.48)), "B": dict(z1=1.12, cx1=(0.42, 0.6)),
                       "C": dict(z1=1.10, cx1=(0.6, 0.62)), "D": dict(z1=1.06, cx1=(0.5, 0.42)),
                       "E": dict(z0=1.0, z1=1.30, cx=(0.5, 0.5), cx1=(0.70, 0.52))}[nome]
                im = camera(pl, p, **cam)
                if nome in "ABC":
                    im = neblina(im, t, chao=0.5, forca=0.30, cor=(0.18, 0.2, 0.24))
                elif nome == "E":
                    im = neblina(im, t, chao=0.6, forca=0.22, cor=(0.35, 0.35, 0.36))
                im = pelicula(im, f)
                osd = [("PLAY", (28, 46), 0.9)] if i < 2.5 * FPS else []
                osd += [("SP  " + CONT[nome], (W - 230, H - 34), 0.75)]
                # o rosto da fita: nas bordas da troca, a imagem já entra/sai com rastro
                im = vhs(im * min(1, p * 4, (1 - p) * 4 + 0.3), f, rastro=max(0, 1 - p * 6) * 0.6, osd=osd)
            o = (np.clip(im, 0, 1) * 255).astype(np.uint8)
            cv2.imwrite(str(TMP / f"f{f:05d}.png"), o); f += 1
        t0 += dur
    return f, marcas


# ---------- som ----------
SR = 48000


def som(total, marcas):
    n = int(total * SR); t = np.arange(n) / SR
    branco = np.random.default_rng(3).normal(0, 1, n)
    rosa = np.convolve(branco, np.ones(8) / 8, "same")
    s = rosa * 10 ** (-40 / 20)                                          # chiado da fita
    s += (np.sin(2 * np.pi * 60 * t) + 0.5 * np.sin(2 * np.pi * 120 * t) + 0.25 * np.sin(2 * np.pi * 180 * t)) * 10 ** (-42 / 20)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * t / 9)
    s += (np.sin(2 * np.pi * 41.2 * t) + np.sin(2 * np.pi * 55.1 * t + 1) * 0.7) * lfo * 10 ** (-24 / 20)   # drone grave
    for nome, a, d in marcas:
        i, j = int(a * SR), int((a + d) * SR)
        if nome.startswith("t") or nome == "fim":                         # estática da troca
            env = np.sin(np.linspace(0, np.pi, j - i)) ** 0.7
            s[i:j] += branco[i:j] * env * 10 ** (-20 / 20)
        if nome in ("c1", "c2", "c3"):                                    # bipe de cartão de emergência
            k = int(0.5 * SR); env = np.minimum(1, np.minimum(np.arange(k), k - np.arange(k)) / 800)
            s[i + 4800:i + 4800 + k] += np.sin(2 * np.pi * 1000 * t[:k]) * env * 10 ** (-28 / 20)
        if nome in "ABCDE" and len(nome) == 1:                            # projetor de 8 mm, bem baixo
            cl = (np.sin(2 * np.pi * 18 * t[i:j]) > 0.95).astype(float)
            s[i:j] += np.convolve(cl * branco[i:j], np.ones(60) / 60, "same") * 10 ** (-30 / 20)
        if nome == "C":                                                   # o "salto": golpe grave
            k = i + int(d * 0.62 * SR); m = int(1.6 * SR)
            s[k:k + m] += np.sin(2 * np.pi * 38 * t[:m]) * np.exp(-t[:m] * 2.2) * 10 ** (-10 / 20)
        if nome == "E":                                                   # algo respira perto do microfone
            env = np.clip((t[i:j] - a) / d, 0, 1) ** 2 * (0.5 + 0.5 * np.sin(2 * np.pi * t[i:j] / 2.4))
            s[i:j] += np.convolve(branco[i:j], np.ones(40) / 40, "same") * env * 10 ** (-26 / 20)
    fade = int(2.5 * SR); s[-fade:] *= np.linspace(1, 0, fade)
    s = np.clip(s / max(1e-6, np.abs(s).max()) * 0.6, -1, 1)
    est = np.stack([s, np.roll(s, 37)], 1)
    with wave.open(str(TMP / "som.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((est * 32767).astype(np.int16).tobytes())


nq, marcas = render()
som(nq / FPS, marcas)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(TMP / "f%05d.png"), "-i", str(TMP / "som.wav"),
                "-vf", "scale=1440:1080:flags=bicubic,gblur=sigma=0.6,pad=1920:1080:240:0:black,format=yuv420p",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", str(SAIDA)], check=True)
print("ok", SAIDA, f"{nq / FPS:.1f}s")
