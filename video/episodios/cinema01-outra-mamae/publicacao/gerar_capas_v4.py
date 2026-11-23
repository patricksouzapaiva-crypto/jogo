"""Capas do O QUE É A CRIATURA? #1 — Outra Mamãe — v4 (23/11).
Pedido do usuário (23/11): "use cenas do filme nas capas como eles fazem" — quadros REAIS do filme (publicacao/quadros,
fora do git), limpos do grão. Pedido do usuário: "melhores ainda, com mais edição, como nos
canais de exemplo" (Refúgio Cult, Derrotando Filmes, Ed Nerd, Thayla Moitinho): cor forte e saturada, o monstro
recortado com brilho em volta, letra Montserrat Black enorme com degradê amarelo→laranja, contorno grosso, sombra 3D,
o nome OUTRA MAMÃE numa tarja vermelha e UMA seta (a capa que mais estourou no nicho usa). Uso: python3 gerar_capas_v4.py"""
from capas_base import *  # noqa: F401,F403 — as ferramentas saíram para capas_base.py (as capas dos Shorts usam as mesmas)

# A — a cena-ícone (a mesma que 3 dos canais grandes usaram): a mãe dobrada debaixo da mesa, sorrindo; "O QUE ELA É?"
im = base("q_704.9.png", 0.74, 0.5, 1.0, limpar=3, luz=1.1)
im = grade(im, sat=1.35, contraste=1.2, brilho=1.12, tinta=(1.05, 0.98, 0.92))
mk = recorte(im, "f_mesa")
im = brilho_em_volta(im, mk, (255, 40, 20), 12, 0.55)
im = vinheta(lado_escuro(im, "esq", 0.5, 0.85), 0.4, 0.7)
c = letreiro(im, [("O QUE", MONT, 150, BRANCO), ("ELA É?", MONT, 170, OURO)], 46, 205, entre=1.0)
tarja(c, "OUTRA MAMÃE", 40, 70, 50)
# seta tirada a pedido do usuário (23/11)
salvar(c, "capa_A_mesa.jpg")

# B — a criatura de perto, clara e limpa, com brilho vermelho; "ELA NÃO É SUA MÃE" (23/11, usuário: "não é um demônio" entregava o veredito)
im = base("q_4898.5.png", 0.0, 0.5, 1.0, espelhar=False, limpar=5, luz=2.2)   # 23/11: rosto à direita, texto à esquerda
im = grade(im, sat=1.25, contraste=1.2, brilho=1.45, tinta=(1.1, 0.97, 0.9), gama=0.8)
mk = recorte(im, "f_criatura")
_a = np.asarray(im); _n = np.empty_like(_a); _d = 150                 # o rosto vai 150 px para a direita
_n[:, _d:] = _a[:, :W - _d]; _n[:, :_d] = cv2.GaussianBlur(_a[:, :_d], (0, 0), 25)
im = vinheta(lado_escuro(Image.fromarray(_n), "esq", 0.5, 0.9), 0.35, 0.75)
c = letreiro(im, [("ELA NÃO É", MONT, 96, BRANCO), ("SUA MÃE", MONT, 128, SANGUE)], 40, 235,
             alinhar="esq", entre=1.02, brilho=(230, 20, 40))
tarja(c, "OUTRA MAMÃE", 40, 70, 50, giro=-3)
salvar(c, "capa_B_sua_mae.jpg")

# C — antes × depois: a mãe sorrindo | a coisa com o mesmo sorriso, corte inclinado; "FINAL EXPLICADO"
e = grade(base("q_609.png", 0.0, 0.40, 1.15, limpar=3, luz=1.2), sat=1.3, contraste=1.15, brilho=1.15, tinta=(1.06, 1.0, 0.94))
d = grade(base("q_4898.5.png", 0.0, 0.5, 1.05, limpar=5, luz=2.2), sat=1.05, contraste=1.3, brilho=1.1, tinta=(0.88, 1.02, 0.98))
ea = np.roll(np.asarray(e), -W // 4 - 110, axis=1); da = np.roll(np.asarray(d)[:, ::-1], W // 4 - 30, axis=1)
yy, xx = np.mgrid[0:H, 0:W]
corte = (xx > W / 2 + (yy - H / 2) * 0.18)[..., None]
a = np.where(corte, da, ea).astype(np.float32)
a *= (1 - 0.8 * np.clip((yy - H * 0.52) / (H * 0.48), 0, 1) ** 1.3)[..., None]
im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
dd = ImageDraw.Draw(im)
for k in range(H):
    cx_ = W / 2 + (k - H / 2) * 0.18
    dd.line([(cx_ - 5, k), (cx_ + 5, k)], fill=(255, 255, 255, 255))
c = letreiro(im.convert("RGB"), [("FINAL", MONT, 120, BRANCO), ("EXPLICADO", MONT, 120, OURO)], W / 2, 455, alinhar="centro", entre=1.0)
tarja(c, "OUTRA MAMÃE", 40, 40, 46, giro=-3)
salvar(c, "capa_C_final.jpg")
