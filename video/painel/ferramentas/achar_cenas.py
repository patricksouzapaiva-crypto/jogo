"""Acha, num filme/trailer, os planos que combinam com cada momento do roteiro (13/11, Ep. 09).

1. Imagem útil: mede a textura por coluna/linha (pega tarja preta E barra colorida de gravação de tela).
2. Cortes de cena: PySceneDetect (detector adaptativo) → lista de planos.
3. Busca por descrição: CLIP (open_clip, ViT-B-32 laion2b) em 3 quadros de cada plano; cada pedido do roteiro vira um
   texto em inglês ("a female shaman dancing in a ritual") e os planos são ordenados pela semelhança.
4. Saída: <saida>/planos.json (todos os planos com tempos) + <saida>/<pedido>.jpg (folha de contato com os melhores,
   para conferir a olho antes de usar) + <saida>/resultado.json.

Uso: python3 achar_cenas.py video.mp4 pedidos.json saida/ [--top 6] [--sem-legenda]
pedidos.json: {"ritual": "a female shaman in colorful clothes dancing in a ritual", ...}
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def recorte_util(video):
    """Retângulo da imagem de verdade. Funciona com tarja preta (cinema) E com as barras coloridas e borradas que
    aparecem em gravação de tela do celular (modo ambiente do YouTube): em vez de procurar preto, mede a TEXTURA
    (variação entre pixels vizinhos) em 24 quadros espalhados; barra lisa ou borrada tem textura ~0."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True).stdout)
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", video],
                                   capture_output=True, text=True).stdout.strip().split(","))
    sw, sh = 480, max(2, round(480 * h / w))
    cols, lins = [], []
    for k in range(24):
        raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{dur * (k + 0.5) / 24:.2f}", "-i", video,
                              "-frames:v", "1", "-vf", f"scale={sw}:{sh},format=gray", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        if len(raw) < sw * sh:
            continue
        g = np.frombuffer(raw[:sw * sh], np.uint8).reshape(sh, sw).astype(np.float32)
        cols.append(np.abs(np.diff(g, axis=0)).mean(0))    # textura vertical de cada coluna
        lins.append(np.abs(np.diff(g, axis=1)).mean(1))    # textura horizontal de cada linha
    # percentil 80 entre quadros: a coluna é imagem se em VÁRIOS quadros tem textura (cenas borradas/escuras não
    # encolhem o recorte; a barra lateral lisa nunca tem)
    col, lin = np.percentile(cols, 80, axis=0), np.percentile(lins, 80, axis=0)
    def faixa(v):
        """Maior trecho contínuo com textura (tolera buracos de até 2%): ignora ícones soltos na barra lateral
        (ex.: o botão do gravador de tela)."""
        lim = 0.35 * np.median(v[len(v) // 3: 2 * len(v) // 3])
        ok = v > lim; gap = max(2, len(v) // 50)
        melhor, ini, buraco = (0, len(v)), None, 0
        for k, b in enumerate(list(ok) + [False] * (gap + 1)):
            if b:
                ini = k if ini is None else ini; buraco = 0; fim = k + 1
            elif ini is not None:
                buraco += 1
                if buraco > gap:
                    if fim - ini > melhor[1] - melhor[0] or melhor == (0, len(v)):
                        melhor = (ini, fim)
                    ini, buraco = None, 0
        return melhor
    x0, x1 = faixa(col); y0, y1 = faixa(lin)
    X0, X1 = round(x0 * w / sw), round(x1 * w / sw); Y0, Y1 = round(y0 * h / sh), round(y1 * h / sh)
    cw, ch = (X1 - X0) // 2 * 2, (Y1 - Y0) // 2 * 2
    return (cw, ch, X0, Y0), dur


def planos(video):
    from scenedetect import detect, AdaptiveDetector
    ps = detect(video, AdaptiveDetector(), show_progress=False)
    # trailer com fusões longas: o detector junta várias cenas num "plano" só → quebra trechos > 6 s em janelas de 3 s
    out = []
    for a, b in ((a.seconds, b.seconds) for a, b in ps):
        n = max(1, round((b - a) / 3)) if b - a > 6 else 1
        out += [(a + (b - a) * k / n, a + (b - a) * (k + 1) / n) for k in range(n)]
    return out


def quadro(video, t, crop):
    vf = (f"crop={crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}," if crop else "") + "scale=384:-2"
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1",
                          "-vf", vf, "-f", "image2pipe", "-c:v", "png", "-"], capture_output=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(raw)).convert("RGB")


def tem_legenda(img):
    """Fração de pixels 'texto branco' na faixa de baixo (72–96% da altura): claro (>200) E com vizinho escuro
    (borda de letra). Legenda gravada dá ~0,5%+; céu/luz lisa quase não tem borda."""
    g = np.asarray(img.convert("L"), np.float32); h = g.shape[0]
    b = g[int(h * 0.72):int(h * 0.96)]
    claro = b > 200
    borda = np.zeros_like(claro)
    borda[:, 1:] |= np.abs(np.diff(b, axis=1)) > 90
    return float((claro & borda).mean())


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    video, pedidos, saida = a[0], json.load(open(a[1])), Path(a[2])
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 6
    saida.mkdir(parents=True, exist_ok=True)
    r = recorte_util(video)
    crop, dur = (r if r else (None, 0))
    print("imagem útil:", crop)
    ps = [p for p in planos(video) if p[1] - p[0] >= 0.8] or [(0.0, dur)]
    print(len(ps), "planos")
    import torch, open_clip
    modelo, _, prep = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
    tok = open_clip.get_tokenizer("ViT-B-32"); modelo.eval()
    imgs, emb, leg = [], [], []
    with torch.no_grad():
        for i, (s, e) in enumerate(ps):
            qs = [quadro(video, s + (e - s) * f, crop) for f in (0.2, 0.5, 0.8)]
            imgs.append(qs[1]); leg.append(max(tem_legenda(q) for q in qs))
            x = modelo.encode_image(torch.stack([prep(q) for q in qs]))
            x = x / x.norm(dim=-1, keepdim=True)
            emb.append(x.mean(0).numpy())
        E = np.stack(emb); E /= np.linalg.norm(E, axis=1, keepdims=True)
        nomes = list(pedidos)
        T = modelo.encode_text(tok([pedidos[n] for n in nomes])).numpy()
        T /= np.linalg.norm(T, axis=1, keepdims=True)
    S = E @ T.T
    sem_leg = "--sem-legenda" in sys.argv
    LIM = 0.0015
    if sem_leg:
        S[np.array(leg) > LIM, :] = -1          # plano com legenda gravada vai pro fim da fila
    json.dump([{"i": i, "ini": round(s, 2), "fim": round(e, 2), "legenda": round(leg[i], 4)} for i, (s, e) in enumerate(ps)],
              open(saida / "planos.json", "w"), indent=1)
    res = {}
    for j, n in enumerate(nomes):
        ordem = np.argsort(-S[:, j])[:top]
        res[n] = [{"plano": int(i), "ini": round(ps[i][0], 2), "fim": round(ps[i][1], 2),
                   "nota": round(float(S[i, j]), 3), "legenda": leg[i] > LIM} for i in ordem]
        # folha de contato: 3 por linha, com tempo e nota
        w, h = imgs[0].size; cols = 3; rows = (len(ordem) + cols - 1) // cols
        folha = Image.new("RGB", (cols * w, rows * (h + 22)), "black"); d = ImageDraw.Draw(folha)
        for k, i in enumerate(ordem):
            x, y = (k % cols) * w, (k // cols) * (h + 22)
            folha.paste(imgs[i], (x, y))
            d.text((x + 4, y + h + 4), f"#{i}  {ps[i][0]:.1f}-{ps[i][1]:.1f}s  {S[i, j]:.3f}" + ("  [LEGENDA]" if leg[i] > LIM else ""),
                   fill="red" if leg[i] > LIM else "white")
        folha.save(saida / f"{n}.jpg", quality=85)
    json.dump({"video": video, "recorte": crop, "pedidos": pedidos, "melhores": res},
              open(saida / "resultado.json", "w"), ensure_ascii=False, indent=1)
    for n in nomes:
        print(n, [(m["ini"], m["fim"], m["nota"]) for m in res[n][:3]])


if __name__ == "__main__":
    main()
