"""Etapa 3: medidas objetivas de continuidade (nos quadros ja preparados, px do jogo).
Gera validacao.json com metricas e alertas por animacao. Os alertas sao para INSPECAO
visual; nao corrigem nada sozinhos."""
import numpy as np, json, os, sys, itertools
from PIL import Image
from scipy import ndimage as ndi
PREP = sys.argv[1]
rel = json.load(open(os.path.join(PREP, "preparo.json")))
saida = {}

def runs(row):  # numero de trechos opacos numa linha
    r = np.concatenate([[0], row.astype(int), [0]]); return int((np.diff(r) == 1).sum())

for esp, d in rel.items():
    W, H = d["canvas"]; px, py = d["pivot"]
    anims = {}
    for q in d["quadros"]:
        anims.setdefault((q["tipo"], q["anim"]), []).append(q)
    saida[esp] = {}
    for (tipo, anim), qs in anims.items():
        qs = sorted(qs, key=lambda q: q["quadro"])
        A = [np.asarray(Image.open(os.path.join(PREP, esp, q["arquivo"]))).astype(int) for q in qs]
        al = [a[..., 3] == 255 for a in A]
        n = len(A)
        area = np.array([m.sum() for m in al])
        top = np.array([np.where(m.any(1))[0].min() for m in al])
        bot = np.array([np.where(m.any(1))[0].max() for m in al])
        # centro do tronco (faixa 30-65% da altura de cada quadro)
        cx = []
        for m, t, b in zip(al, top, bot):
            h = b - t + 1; band = m[int(t + .30 * h):int(t + .65 * h)]
            xs = np.where(band.any(0))[0]; cx.append((xs.min() + xs.max()) / 2)
        cx = np.array(cx)
        # diferenca entre quadros (pixels que mudam de cor ou de alpha), em % da area
        def dif(i, j):
            # compensa o sobe e desce de ate 1 px (movimento intencional do corpo) antes de comparar
            melhor = 1e9
            for dy in (-1, 0, 1):
                a, b = A[i], np.roll(A[j], dy, 0)
                ai, bj = al[i], np.roll(al[j], dy, 0)
                mud = (ai != bj) | (ai & bj & (np.abs(a[..., :3] - b[..., :3]).sum(-1) > 60))
                melhor = min(melhor, mud.sum() / max(1, (ai | bj).sum()) * 100)
            return melhor
        cons = [dif(i, (i + 1) % n) for i in range(n)]       # inclui ultimo->primeiro
        med = np.median(cons[:-1]) if n > 2 else cons[0]
        # patas visiveis: trechos opacos na faixa de baixo (3 linhas acima da base)
        legs = []
        for m, b in zip(al, bot):
            legs.append(max(runs(m[y]) for y in range(max(0, b - 4), b - 1)))
        # ordem: existe ordem ciclica com movimento bem menor? (so caminhada, 8 quadros)
        ordem_sug = None
        if tipo == "walk":
            D = np.array([[dif(i, j) if i != j else 0 for j in range(n)] for i in range(n)])
            atual = sum(D[i, (i + 1) % n] for i in range(n))
            best, bp = atual, None
            for perm in itertools.permutations(range(1, n)):
                p = (0,) + perm
                s = sum(D[p[i], p[(i + 1) % n]] for i in range(n))
                if s < best - 1e-9: best, bp = s, p
            if bp and best < atual * 0.85:
                ordem_sug = dict(ordem=list(bp), reducao_pct=round((1 - best / atual) * 100, 1))
        alertas = []
        if tipo == "walk":
            dev = np.abs(area - np.median(area)) / np.median(area) * 100
            for i in np.where(dev > 10)[0]: alertas.append(f"quadro {i}: area {dev[i]:.0f}% diferente da mediana (tamanho do corpo mudando?)")
            for i in range(n):
                j = (i + 1) % n
                if abs(cx[j] - cx[i]) > 2: alertas.append(f"quadro {i}->{j}: tronco salta {cx[j]-cx[i]:+.1f} px na horizontal")
                if abs(top[j] - top[i]) > 3: alertas.append(f"quadro {i}->{j}: topo salta {top[j]-top[i]:+d} px (balanco > 3 px)")
        for i in range(n - 1):
            if cons[i] < 3: alertas.append(f"quadros {i} e {i+1} quase iguais ({cons[i]:.1f}% muda): repetido?")
        if n > 2 and cons[-1] > 1.8 * med and cons[-1] > 8:
            alertas.append(f"emenda do loop {n-1}->0 muda {cons[-1]:.0f}% (mediana {med:.0f}%): ruptura no loop")
        for i in range(n - 1):
            if cons[i] > 2.2 * med and cons[i] > 12: alertas.append(f"quadro {i}->{i+1}: mudanca brusca ({cons[i]:.0f}% vs mediana {med:.0f}%)")
        if ordem_sug: alertas.append(f"ordem alternativa com {ordem_sug['reducao_pct']}% menos movimento: {ordem_sug['ordem']} (conferir a olho)")
        saida[esp][f"{tipo}:{anim}"] = dict(
            quadros=n, area=area.tolist(), topo=top.tolist(), base=bot.tolist(), centro_tronco=cx.round(1).tolist(),
            patas_visiveis=legs, mudanca_entre_quadros_pct=[round(c, 1) for c in cons], alertas=alertas, ordem_sugerida=ordem_sug)
json.dump(saida, open(os.path.join(PREP, "validacao.json"), "w"), indent=1, ensure_ascii=False)
for esp, an in saida.items():
    print("=" * 10, esp)
    for k, v in an.items():
        print(f"  {k:22s} patas={v['patas_visiveis']} muda%={v['mudanca_entre_quadros_pct']}")
        for a in v["alertas"]: print("      ! " + a)
