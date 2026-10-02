"""Etapa 2b (v2): melhora a CAMINHADA sem redesenhar e sem recortar partes do corpo.

1. Textura estavel: na regiao do corpo (acima das patas), cada pixel que difere so um pouco da
   cor mais comum naquela posicao ao longo do ciclo recebe essa cor. Remove a "fervura" de
   manchas/la/penas. Diferencas grandes (contorno, cabeca que mexe, cauda) ficam como estao.
2. Sobe e desce de 1 px (so nos ciclos que nao tem nenhum): na passagem o corpo sobe 1 px; a
   linha do quadril e duplicada (a perna "estica" 1 px), os pes continuam no chao. Nada e
   recortado nem girado.
3. Ritmo: quadros quase repetidos (movimento ate o proximo < 55% da mediana) ficam com metade
   da duracao, e o tempo economizado e dividido entre os outros. Assim some a pausa no ciclo sem
   criar ritmo irregular. A duracao total do ciclo nao muda.
4. Pose de parado por direcao: o quadro com as patas mais juntas e os dois pes no chao.
5. Correcao provisoria (pixel) do Gruntho de costas: os quadros 3 e 7 passam a ser os quadros com
   as duas patas no chao (2 e 6) com a pata ESQUERDA levantada, transplantada (espelhada) da pata
   direita levantada dos quadros 3 e 7 originais. O resto do corpo e a luz ficam intactos.
"""
import numpy as np, json, os, sys, shutil
from PIL import Image
PREP, OUT = sys.argv[1], sys.argv[2]
FPS = {"penala": 10, "pato": 9, "ovelha": 7, "gruntho": 8, "vaca": 6}
# (especie, direcao): {quadro_novo: (quadro_base_patas_no_chao, quadro_com_pata_direita_levantada)}
TRANSPLANTE_PATA = {("gruntho", "up"): {3: (2, 3), 7: (6, 7)}}
DIST_TEXTURA = 110       # soma |dR|+|dG|+|dB| maxima para considerar "mesma cor com variacao"
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(PREP, OUT)
rel = json.load(open(os.path.join(PREP, "preparo.json")))

def carrega(esp, dn, c):
    return np.asarray(Image.open(os.path.join(PREP, esp, f"{esp}_walk_{dn}_{c}.png"))).copy()

def linha_quadril(A, py):
    """primeira linha (de baixo para cima) em que o corpo fica largo: acima dela e corpo, abaixo patas"""
    al = np.median(np.stack([a[..., 3] == 255 for a in A]).astype(float), axis=0) > 0.5
    larg = al.sum(1); ys = np.where(larg > 0)[0]; top = ys.min()
    lim = 0.62 * larg.max()
    for y in range(py, top, -1):
        if larg[y] >= lim: return y
    return int(top + 0.6 * (py - top))

def sinal_passo(A, py, lateral):
    s = []
    for a in A:
        al = a[..., 3] == 255
        if lateral:   # abertura entre os pes (4 linhas de baixo)
            xs = np.where(al[py - 3:py + 1].any(0))[0]; s.append(xs.max() - xs.min() + 1 if len(xs) else 0)
        else:         # largura de contato com o chao (2 linhas de baixo): pe levantado = menos contato
            s.append(int(al[py - 1:py + 1].any(0).sum()))
    return np.array(s, float)

def mov(a, b, y0):
    A_, B_ = a[y0:, :, 3] == 255, b[y0:, :, 3] == 255
    return (A_ ^ B_).sum() / max(1, (A_ | B_).sum())

log = {}
for esp, d in rel.items():
    W, H = d["canvas"]; px, py = d["pivot"]
    d.setdefault("walk_duracoes", {}); d.setdefault("parado", {}); log[esp] = {}
    for dn in ["down", "left", "right", "up"]:
        A = [carrega(esp, dn, c) for c in range(8)]
        lateral = dn in ("left", "right")
        hip = linha_quadril(A, py)
        notas = []
        rigado = dn in d.get("caminhada_gerada_por_esqueleto", [])
        if rigado:
            notas.append("caminhada gerada pelo esqueleto de patas (corpo identico em todos os quadros)")
        # 5. transplante da pata (Gruntho de costas) - so se a direcao NAO veio do esqueleto
        for c, (base_i, src_i) in ({} if rigado else TRANSPLANTE_PATA.get((esp, dn), {})).items():
            base, src = A[base_i].copy(), A[src_i]
            # regiao onde a pata direita levantada difere do quadro com as patas no chao (lado direito)
            difere = ((base[..., 3] != src[..., 3]) |
                      (np.abs(base[..., :3].astype(int) - src[..., :3].astype(int)).sum(-1) > 90))
            difere[:, :px + 1] = False
            difere[:hip - 10] = False
            ys, xs = np.where(difere)
            t = int(ys.min()) - 1
            novo = base.copy()
            # lado direito: pata no chao (do quadro base); lado esquerdo: pata direita levantada espelhada
            for x in range(0, px + 1):
                xm = 2 * px - x
                if 0 <= xm < W:
                    novo[t:, x] = src[t:, xm]
            A[c] = novo
            notas.append(f"quadro {c}: pata esquerda levanta (base {base_i}, pata espelhada do quadro {src_i}, linhas {t}-{py})")
        # 1. textura estavel no corpo (linhas 0..hip)
        pilha = np.stack(A)                       # 8,H,W,4
        trocados = 0
        for y in range(0, hip + 1):
            for x in range(W):
                cores = [tuple(pilha[i, y, x, :3]) for i in range(8) if pilha[i, y, x, 3] == 255]
                if len(cores) < 5: continue
                vals, cont = np.unique(np.array(cores), axis=0, return_counts=True)
                moda = vals[cont.argmax()]
                if cont.max() < 4: continue
                for i in range(8):
                    if pilha[i, y, x, 3] != 255: continue
                    dist = np.abs(pilha[i, y, x, :3].astype(int) - moda.astype(int)).sum()
                    if 0 < dist <= DIST_TEXTURA:
                        pilha[i, y, x, :3] = moda; trocados += 1
        A = [pilha[i].copy() for i in range(8)]
        area_corpo = sum(int((a[:hip + 1, :, 3] == 255).sum()) for a in A)
        notas.append(f"textura estabilizada em {trocados} px ({trocados / max(1, area_corpo) * 100:.1f}% do corpo)")
        # 2. sobe e desce (so se o desenho nao tem)
        topos = [int(np.where((a[..., 3] == 255).any(1))[0].min()) for a in A]
        sinal = sinal_passo(A, py, lateral)
        bob = [0] * 8
        if max(topos) - min(topos) <= 1 and sinal.max() > sinal.min():
            # ritmo periodico: 2 passos por ciclo de 8 -> o corpo sobe 2 quadros a cada 4 (na passagem).
            # So a FASE e escolhida pelos pes: passagem = patas juntas (lado) / um pe no ar (frente/costas).
            alvo = -(sinal - sinal.mean()) / (sinal.std() + 1e-6)
            modelo = np.array([0, 1, 1, 0, 0, 1, 1, 0], float)
            fase = max(range(4), key=lambda f: float(np.dot(np.roll(modelo, f) - 0.5, alvo)))
            bob = [int(b) for b in np.roll(modelo, fase)]
            for i in range(8):
                if bob[i]:
                    a = A[i]; novo = a.copy()
                    novo[0:hip] = a[1:hip + 1]          # corpo sobe 1 px; linha do quadril fica duplicada
                    A[i] = novo
            notas.append(f"sobe e desce de 1 px: {''.join('↑' if b else '·' for b in bob)} (quadril na linha {hip})")
        else:
            notas.append("sobe e desce ja desenhado: mantido")
        # 3. ritmo: so os quadros quase repetidos ficam mais curtos
        y0 = max(0, hip - 2)
        m = np.array([mov(A[i], A[(i + 1) % 8], y0) for i in range(8)])
        base = 1.0 / FPS[esp]
        fator = np.where(m < 0.55 * np.median(m), 0.5, 1.0)
        dur = fator / fator.sum() * 8 * base
        d["walk_duracoes"][dn] = [round(float(x), 4) for x in dur]
        curtos = [i for i in range(8) if fator[i] < 1]
        notas.append(("quadros quase repetidos encurtados: " + ", ".join(map(str, curtos))) if curtos else "ritmo uniforme")
        # 4. pose de parado: patas mais juntas e os dois pes no chao
        if lateral:
            score = sinal          # menor abertura
        else:
            contato = sinal_passo(A, py, False)
            score = -contato       # mais contato com o chao
        score = np.asarray(score, float) + np.array(bob) * (abs(np.ptp(score)) + 1)   # evita quadro "subido"
        par = int(np.argmin(score))
        d["parado"][dn] = par
        notas.append(f"parado = quadro {par}")
        for c in range(8):
            Image.fromarray(A[c], "RGBA").save(os.path.join(OUT, esp, f"{esp}_walk_{dn}_{c}.png"))
        log[esp][dn] = notas
        print(f"{esp:8s} {dn:5s} | " + " | ".join(notas))
    d["versao"] = "v2"
json.dump(rel, open(os.path.join(OUT, "preparo.json"), "w"), indent=1, ensure_ascii=False)
json.dump(log, open(os.path.join(OUT, "melhorias_v2.json"), "w"), indent=1, ensure_ascii=False)
