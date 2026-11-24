"""Cartões de capítulo do Ep. 12, o EMAKI VIVO (24/11). Pedido do usuário: "vamos aumentar o nível também dos capítulos".
As camadas foram geradas pelo usuário (PROMPTS_CAPITULOS.md) e recortadas do verde com recortar.py (capitulos/camadas/).
A sequência (7,6 s, 30 qps, 1920×1080):
  0,0–0,8  a mesa de laca à luz de vela surge do escuro; a fumaça de incenso atravessa; o objeto-símbolo do capítulo
  0,6–2,2  o ROLO DESENROLA da direita para a esquerda (como se lê no Japão) — som do papel
  1,9–3,6  a GRAVURA REAL do capítulo nasce no papel por uma mancha de nanquim que se espalha (com respingos)
  2,9–4,0  o pincel escreve o número na vertical (第一章 … 最終章), um traço por vez — som do pincel
  4,1–4,7  o CARIMBO de pedra desce, bate (鬼, em vermelho) e sobe — carimbo + taiko, a câmera treme
  4,6–5,8  o título em português e o ano aparecem embaixo, num movimento de pincel
  5,8–7,6  respiro: a vela tremendo, a câmera chegando perto; escurece no fim (o corte para a cena)
Uso: python3 emaki.py [N ...] [--quadros t1,t2,...]    (N = 1..7, 0 = a história)"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent; EP = AQUI.parent; CAM = AQUI / "camadas"
FONTES = EP.parents[1] / "painel" / "fontes"; SONS = EP.parents[1] / "painel" / "sons"
W, H, FPS, DUR = 1920, 1080, 30, 7.6
CAPS = {
    1: ("A mulher que virou demônio", "séc. IX", "m_kanawa", "10_gotoku_01"),
    2: ("A porta do demônio", "713 · hoje", "m_ibaraki_esboco", "11_macaco_madeira_01"),
    3: ("O oni que bebia saquê", "990", "shuten_rolo_cbl", "12_sakazuki_01"),
    4: ("O demônio que virou deus", "903", "m_michizane_trovao", "13_galho_ume_01"),
    5: ("As regras", "como sobreviver", "kyosai_4", "14_ema_01"),
    6: ("Os piores", "1251 · 2022", "ushioni_rolo", "15_pedra_vulcanica_01"),
    7: ("O desfile dos cem demônios", "956", "ROLO_hyakki_aic", "16_lanterna_chochin_02"),
    0: ("A sétima noite", "hoje", "ritual_sekien", "17_boneco_palha_01"),
}
NUM = "〇一二三四五六七"
KX, SX, SY = 1510, 1335, 128   # coluna do número, carimbo (x) e altura do carimbo abaixo do centro do rolo


# ------------------------------------------------------------------ utilidades
def ler(nome, larg=None, alt=None):
    """RGBA float premultiplicado."""
    p = CAM / (nome + ".png") if not str(nome).startswith("/") else Path(nome)
    im = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3: im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255
    if larg or alt:
        h, w = im.shape[:2]; e = (larg / w) if larg else (alt / h)
        im = cv2.resize(im, (max(1, round(w * e)), max(1, round(h * e))), interpolation=cv2.INTER_AREA)
    im[..., :3] *= im[..., 3:4]
    return im


def por(tela, img, cx, cy, esc=1.0, ang=0.0, alfa=1.0, sombra=0.0):
    """Cola img (premult.) com centro em (cx, cy), escala e rotação; sombra macia embaixo/direita."""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, esc); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    if sombra:
        Ms = M.copy(); Ms[0, 2] += 18; Ms[1, 2] += 26
        a = cv2.warpAffine(img[..., 3], Ms, (W, H), flags=cv2.INTER_LINEAR)
        a = cv2.GaussianBlur(a, (0, 0), 22) * sombra * alfa
        tela[..., :3] *= (1 - a[..., None])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR) * alfa
    tela[..., :3] = tela[..., :3] * (1 - o[..., 3:4]) + o[..., :3]


def suave(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def sai(x):
    x = np.clip(x, 0, 1); return 1 - (1 - x) ** 3


def texto_rgba(txt, fonte, tam, cor, vertical=False, esp=1.0):
    F = ImageFont.truetype(str(FONTES / fonte), tam)
    if vertical:
        hs = [F.getbbox(c) for c in txt]; lw = max(b[2] - b[0] for b in hs) + 20; lh = int(tam * esp)
        im = Image.new("RGBA", (lw, lh * len(txt) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for k, c in enumerate(txt):
            b = F.getbbox(c); d.text(((lw - (b[2] - b[0])) / 2 - b[0], k * lh - b[1] + 10), c, font=F, fill=cor)
    else:
        b = F.getbbox(txt); im = Image.new("RGBA", (b[2] - b[0] + 20, b[3] - b[1] + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - b[0], 10 - b[1]), txt, font=F, fill=cor)
    a = np.asarray(im).astype(np.float32) / 255; a[..., :3] *= a[..., 3:4]
    return a


class Cartao:
    def __init__(self, n):
        self.n = n; titulo, ano, arte, objeto = CAPS[n]
        mesa = cv2.cvtColor(cv2.imread(str(CAM / "01_mesa_laca_01.png")), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        self.mesa = cv2.resize(mesa, (int(W * 1.08), int(H * 1.08)), interpolation=cv2.INTER_CUBIC)
        fum = cv2.cvtColor(cv2.imread(str(CAM / "21_fumaca_incenso_02.png")), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        self.fumaca = cv2.resize(fum, (W, int(W * fum.shape[0] / fum.shape[1])))
        # o rolo: papel (05) recortado na área útil; o rolinho (03) em pé
        self.papel = ler("05_papel_washi_01", larg=1480)                 # ~1480×496
        rolo = ler("03_rolo_fechado_01"); rolo = np.ascontiguousarray(np.rot90(rolo, 1))
        e = (self.papel.shape[0] + 70) / rolo.shape[0]
        self.rolo = cv2.resize(rolo, (round(rolo.shape[1] * e), round(rolo.shape[0] * e)), interpolation=cv2.INTER_AREA)
        self.vara = cv2.resize(self.rolo, (round(self.rolo.shape[1] * 0.55), self.rolo.shape[0]), interpolation=cv2.INTER_AREA)
        # a gravura real do capítulo (sem crédito: o cartão é nosso; o crédito está na cena dela)
        art = cv2.cvtColor(cv2.imread(str(next(p for p in (EP / "reais" / (arte + ".jpg"), EP / "reais" / (arte + ".png")) if p.exists()))),
                           cv2.COLOR_BGR2RGB).astype(np.float32) / 255
        aw, ah = 920, 370; e = min(aw / art.shape[1], ah / art.shape[0])   # cabe na área útil do papel (sem as faixas de brocado)
        self.arte = cv2.resize(art, (round(art.shape[1] * e), round(art.shape[0] * e)), interpolation=cv2.INTER_AREA)
        self.mancha = ler("18_mancha_nanquim_03")[..., 3]
        r = ler("20_respingos_nanquim_01", larg=1100)
        lum = (r[..., :3] / np.maximum(r[..., 3:4], 1e-4)).mean(2)          # só a tinta preta (o halo branco sai)
        r[..., 3] *= np.clip((0.55 - lum) / 0.4, 0, 1) ** 1.2; r[..., :3] = 0.04 * r[..., 3:4]
        self.respingo = r
        self.objeto = ler(objeto, alt=250 if n not in (4, 6) else 170)
        self.vela = ler("08_vela_warosoku_01", alt=470)
        self.hanko = ler("06_hanko_04", alt=240)   # 24/11: a foto vista de cima que o usuário mandou
        self.kanji = texto_rgba("第" + NUM[n] + "章" if n else "最終章", "YujiSyuku-400.ttf", 104, (16, 12, 10, 255), vertical=True, esp=1.05)
        self.selo = self._selo()
        self.t_cap = texto_rgba((f"CAPÍTULO {n}" if n else "A HISTÓRIA"), "ShipporiMincho-800.ttf", 30, (201, 162, 92, 255))
        self.t_tit = texto_rgba(titulo.upper(), "ShipporiMincho-800.ttf", 62, (238, 226, 204, 255))
        self.t_ano = texto_rgba(ano, "ShipporiMincho-800.ttf", 34, (196, 46, 40, 255))
        self.rng = np.random.default_rng(1200 + n)

    def _selo(self):
        s = 112; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((4, 4, s - 4, s - 4), 10, fill=(176, 28, 26, 255))
        F = ImageFont.truetype(str(FONTES / "ShipporiMincho-800.ttf"), 80); b = F.getbbox("鬼")
        d.text(((s - (b[2] - b[0])) / 2 - b[0], (s - (b[3] - b[1])) / 2 - b[1]), "鬼", font=F, fill=(0, 0, 0, 0))
        a = np.asarray(im).astype(np.float32) / 255
        # tinta de carimbo: falhas e grão
        g = np.random.default_rng(5).random(a.shape[:2]).astype(np.float32)
        g = cv2.GaussianBlur(g, (0, 0), 1.2); a[..., 3] *= np.clip((g - 0.18) * 3, 0.55, 1)
        a[..., :3] *= a[..., 3:4]
        return a

    # ------------------------------------------------------------------ um quadro
    def quadro(self, t):
        luz = 1 + 0.05 * np.sin(t * 13.1) + 0.03 * np.sin(t * 29.7 + 1.3) + 0.02 * self.rng.standard_normal()
        # mesa (desliza bem devagar)
        dx = int(40 * t / DUR); tela = np.zeros((H, W, 4), np.float32)
        tela[..., :3] = self.mesa[30:30 + H, 40 + dx // 2:40 + dx // 2 + W]; tela[..., 3] = 1
        # objeto-símbolo à esquerda, vela à direita
        oh, ow = self.objeto.shape[:2]   # canto de baixo à esquerda, longe do título
        por(tela, self.objeto, max(150, ow / 2 + 20), 1040 - oh / 2, ang=-4, sombra=0.75)
        por(tela, self.vela, 1760, 1080 - self.vela.shape[0] / 2 - 20, sombra=0.5)
        # ROLO: x_rolo vai de 1640 (fechado à direita) até 260 (aberto)
        u = sai((t - 0.6) / 1.6); xr = 1660 - 1400 * u; cy = 470
        ph, pw = self.papel.shape[:2]; x_dir = 1660; y0 = int(cy - ph / 2)
        vis = int(max(0, x_dir - xr))
        if vis > 4:
            tira = self.papel[:, pw - vis:pw] if vis <= pw else self.papel
            sombra_area = np.zeros((H, W), np.float32)
            x0 = int(x_dir - tira.shape[1])
            sombra_area[y0 + 16:y0 + ph + 30, x0 + 10:x_dir + 14] = 0.55
            sombra_area = cv2.GaussianBlur(sombra_area, (0, 0), 18); tela[..., :3] *= (1 - sombra_area[..., None])
            reg = tela[y0:y0 + ph, x0:x_dir]
            reg[..., :3] = reg[..., :3] * (1 - tira[..., 3:4]) + tira[..., :3]
            # a GRAVURA nasce na tinta (multiplicada no papel, só onde o papel já abriu)
            ah, aw = self.arte.shape[:2]; ax0 = 300 + (950 - aw) // 2; ay0 = int(cy - ah / 2)
            k = suave((t - 1.9) / 1.7)
            if k > 0:
                ms = cv2.resize(self.mancha, (int(aw * (0.3 + 1.5 * k)), int(ah * (0.3 + 1.5 * k))))
                m = np.zeros((ah, aw), np.float32); mh_, mw_ = ms.shape
                yy, xx = (ah - mh_) // 2, (aw - mw_) // 2
                sy0, sx0 = max(0, -yy), max(0, -xx); dy0, dx0 = max(0, yy), max(0, xx)
                hh, ww = min(mh_ - sy0, ah - dy0), min(mw_ - sx0, aw - dx0)
                m[dy0:dy0 + hh, dx0:dx0 + ww] = ms[sy0:sy0 + hh, sx0:sx0 + ww]
                m = np.clip(m * 1.6, 0, 1) * np.clip(k * 3, 0, 1)
                m = np.maximum(m, suave((t - 3.2) / 0.6))           # no fim a gravura fica inteira
                corte = max(0, int(x0 - ax0))
                if corte < aw:
                    alvo = tela[ay0:ay0 + ah, ax0 + corte:ax0 + aw, :3]
                    a_ = self.arte[:, corte:]; mm = m[:, corte:, None] * 0.93
                    alvo[:] = alvo * (1 - mm) + alvo * (a_ ** 1.1) * mm   # multiplicar: tinta no papel
            sp = suave((t - 1.9) / 0.25) * (1 - suave((t - 3.0) / 0.8))
            if sp > 0 and x0 < 900:
                r = self.respingo; por(tela, r, 780, cy, esc=0.55, alfa=sp * 0.8)
            # o NÚMERO, escrito de cima para baixo
            kh = self.kanji.shape[0]; kx, ky = KX, int(cy - kh / 2)   # coluna centrada na faixa livre do papel
            w_ = suave((t - 2.9) / 1.1)
            if w_ > 0 and x0 < kx - 80:
                kj = self.kanji.copy(); corte_y = int(kh * w_); kj[corte_y:] = 0
                borda = slice(max(0, corte_y - 30), corte_y)
                kj[borda] *= np.linspace(1, 0, borda.stop - borda.start, dtype=np.float32)[:, None, None]
                por(tela, kj, kx, ky + kh / 2)
            # o CARIMBO
            if t >= 4.35:
                por(tela, self.selo, SX, cy + SY, ang=0, alfa=min(1, (t - 4.35) / 0.05) * 0.92)
        # rolinhos por cima do papel (o que se move e a vara fixa)
        por(tela, self.vara, x_dir + 6, cy, sombra=0.5)
        if u < 0.999 or True:
            por(tela, self.rolo, xr - 4, cy, sombra=0.6)
        # a pedra do carimbo: desce, bate, sobe
        if 4.05 <= t <= 4.85:
            if t < 4.35: e = 1.6 - 0.6 * suave((t - 4.05) / 0.3); a = suave((t - 4.05) / 0.15); yy = cy + SY - 220 * (1 - suave((t - 4.05) / 0.3))
            else: e = 1.0 + 0.25 * suave((t - 4.45) / 0.4); a = 1 - suave((t - 4.5) / 0.35); yy = cy + SY - 260 * suave((t - 4.45) / 0.4)
            por(tela, self.hanko, SX, yy - 62, esc=e, ang=0, alfa=a, sombra=0.6 * a)   # reto, o bloco exatamente sobre a marca
        # título e ano embaixo (pincel: revela da esquerda para a direita, borda macia)
        for img, y, t0 in ((self.t_cap, 790, 4.6), (self.t_tit, 850, 4.75), (self.t_ano, 922, 5.2)):
            r = suave((t - t0) / 0.9)
            if r > 0:
                im = img.copy(); w = im.shape[1]; c = int(w * r)
                rampa = np.clip((c - np.arange(w)) / 60, 0, 1).astype(np.float32)
                im *= rampa[None, :, None]; por(tela, im, 960, y)   # centrado no rolo
        # fumaça de incenso atravessando (tela = screen)
        fy = int(500 - 90 * t / DUR); fh = self.fumaca.shape[0]
        f = np.zeros((H, W, 3), np.float32); y1 = max(0, fy); y2 = min(H, fy + fh)
        if y2 > y1: f[y1:y2] = self.fumaca[y1 - fy:y2 - fy]
        f *= 0.35 * suave(t / 1.5); tela[..., :3] = 1 - (1 - tela[..., :3]) * (1 - f)
        # luz da vela: quente e tremendo, cantos no escuro
        yy, xx = np.ogrid[:H, :W]
        rad = np.exp(-(((xx - 1700) / 1250.0) ** 2 + ((yy - 520) / 900.0) ** 2)) * 0.55 + 0.55
        img = tela[..., :3] * rad[..., None] * luz * np.array([1.06, 0.98, 0.88], np.float32)
        # câmera: chega perto devagar + tremor no carimbo
        z = 1.0 + 0.045 * suave(t / DUR)
        tremor = 6 * np.exp(-(t - 4.35) * 9) * np.sin((t - 4.35) * 70) if t >= 4.35 else 0
        M = cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z); M[1, 2] += tremor
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        # entra do escuro e escurece no fim
        img *= suave(t / 0.8) * (1 - 0.85 * suave((t - 6.9) / 0.7))
        return np.clip(img, 0, 1)

    def render(self, saida, quadros=None):
        if quadros:
            for t in quadros:
                cv2.imwrite(str(saida).replace(".mp4", f"_{t:.2f}.jpg"), cv2.cvtColor((self.quadro(t) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
            return
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", str(saida)],
                             stdin=subprocess.PIPE)
        for k in range(int(DUR * FPS)):
            p.stdin.write((self.quadro(k / FPS) * 255).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()


def som(saida, mudo):
    """Papel desenrolando (0,6 s), pincel (2,9 s), carimbo + taiko (4,35 s), tinta (1,9 s)."""
    ev = [("ep10_desenrolar", 0.55, -12), ("ep08_tinta", 1.85, -16), ("ep08_pincel", 2.9, -14), ("ep08_carimbo", 4.3, -9),
          ("ep08_taiko", 4.33, -11), ("ep08_pincel", 4.7, -20)]
    ins, f = ["-i", str(mudo)], []
    for k, (s, t, db) in enumerate(ev, 1):
        ins += ["-i", str(SONS / f"{s}.mp3")]
        f.append(f"[{k}:a]aformat=channel_layouts=stereo,volume={db}dB,adelay={int(t * 1000)}:all=1[s{k}]")
    f.append("".join(f"[s{k}]" for k in range(1, len(ev) + 1)) + f"amix=inputs={len(ev)}:normalize=0,apad,atrim=0:{DUR},afade=t=out:st={DUR - 0.6}:d=0.6[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(f), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", str(saida)], check=True)


if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(CAPS)
    qd = next((a.split(",") for a in sys.argv if a.startswith("--quadros")), None)
    (EP / "cartoes").mkdir(exist_ok=True)
    for n in ns:
        c = Cartao(n)
        if qd:
            c.render(Path("/dev/shm") / f"emaki_cap{n}.mp4", [float(x) for x in sys.argv[sys.argv.index(next(a for a in sys.argv if a.startswith("--quadros"))) + 1].split(",")])
            continue
        mudo = Path("/dev/shm") / f"emaki_cap{n}_mudo.mp4"
        c.render(mudo); som(EP / "cartoes" / f"cap{n}.mp4", mudo); mudo.unlink()
        print("ok cartão", n, flush=True)
