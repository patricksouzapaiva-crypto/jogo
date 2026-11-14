"""Revisão antes de mandar QUALQUER rascunho ao usuário (14/11). Nasceu da lista de erros do rascunho 1 do Ep. 09:
voz mudando de timbre e palavra lida errada; kanji escuro ou rápido demais para ler; foco redondo sem sentido; zoom no
lugar errado; mesma imagem repetida; trecho de filme travando (desacelerado pelo motor) ou com ícone da gravação;
crédito coberto pela legenda; Vigia surgindo de repente; música abafando a voz.

Uso (de dentro da pasta do episódio):
  python3 ../../painel/ferramentas/revisar.py voz        → frases em que o Whisper não ouviu o que está no roteiro
  python3 ../../painel/ferramentas/revisar.py roteiro    → checagens no roteiro.json (antes de renderizar)
  python3 ../../painel/ferramentas/revisar.py video previas/x.mp4 [log]
        → folhas com 2 quadros de CADA cena (para olhar uma por uma) + avisos do log (vídeo desacelerado, mix)
Sai com código 1 se houver ERRO (aviso não bloqueia)."""
import difflib, json, re, subprocess, sys, unicodedata
from collections import Counter
from pathlib import Path

AQUI = Path.cwd()
PAINEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAINEL))
ERROS, AVISOS = [], []
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())
PEQUENAS = {"a", "o", "e", "de", "da", "do", "que", "um", "uma", "em", "no", "na", "se", "pra", "pro", "os", "as"}


def voz():
    """Compara, frase por frase, o roteiro com o que o Whisper ouviu (audio/ouvidas.json do alinhar.py)."""
    sys.path.insert(0, str(AQUI))
    import falas as F
    fl = F.ler()[0] + [F.VINHETA]
    ouv = [norm(w[0]) for w in json.load(open(AQUI / "audio" / "ouvidas.json"))]
    pal = [norm(w) for f in fl for w in f.split()]
    sm = difflib.SequenceMatcher(None, pal, ouv, autojunk=False)
    ok = [False] * len(pal)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            ok[a + k] = True
    k = 0
    for i, f in enumerate(fl):
        n = len(f.split()); seg = list(zip(pal[k:k + n], ok[k:k + n])); k += n
        faltam = [w for w, o in seg if not o and w and w not in PEQUENAS]
        taxa = sum(o for _, o in seg) / max(1, len(seg))
        if faltam and (taxa < 0.8 or len(faltam) >= 2):
            AVISOS.append(f"voz {i:3d} ({taxa:.0%}) não ouvi: {' '.join(faltam)}  ← {f[:80]}")
    print("Ouvir com atenção as frases acima (pode ser só o Whisper, ou o TTS leu errado).")


def roteiro():
    from PIL import Image, ImageStat
    r = json.load(open(AQUI / "roteiro.json"))
    cenas = [c for b in r["batidas"] for c in ([b["cena"]] if b.get("cena") else []) + b.get("cenas", [])]
    usos = Counter(Path(c["imagem"]).name for c in cenas if c.get("imagem") and not c.get("vigia"))
    for nome, n in usos.items():
        if n > 3:
            AVISOS.append(f"imagem repetida {n}x: {nome}")
    for i, c in enumerate(cenas):
        if c.get("dof"):
            ERROS.append(f"cena {i}: foco redondo (dof) — o usuário reprovou")
        ks = c.get("kanji") or []
        ks = ks if isinstance(ks, list) else [ks]
        arq = c.get("imagem")
        for k in ks:
            if k.get("modo") == "tinta" and arq and (AQUI / arq).exists():   # tinta = traço preto: some no escuro
                im = Image.open(AQUI / arq).convert("L"); w, h = im.size
                x, y = k.get("x", 0.5), k.get("y", 0.5)
                lum = ImageStat.Stat(im.crop((int(max(0, x - 0.12) * w), int(max(0, y - 0.2) * h),
                                              int(min(1, x + 0.12) * w), int(min(1, y + 0.2) * h)))).mean[0] / 255
                if lum < 0.45:
                    ERROS.append(f"cena {i}: kanji '{k.get('texto')}' em tinta preta sobre fundo escuro ({lum:.2f}) — use 'luz' ou 'sangue'")
        z = c.get("zoom") or [1, 1]
        if max(z) > 1.45 and not c.get("_c3d"):
            AVISOS.append(f"cena {i}: zoom {max(z):.2f} em {Path(str(arq)).name} — conferir se o assunto inteiro cabe no quadro")
    if r.get("abertura") and r.get("abertura", {}).get("antes_da_batida"):
        ERROS.append("cartão de abertura no meio do Vigia (corta e volta) — use titulo_ep (título ao lado do Vigia)")


def video(mp4, log=None):
    from PIL import Image, ImageDraw
    t = json.load(open(str(mp4) + ".tempos.json"))
    cenas = t.get("cenas") or []
    if not cenas:
        ERROS.append("o .tempos.json não tem a lista de cenas (renderizar de novo com o gerar.py atual)"); return
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout)
    pasta = Path("/tmp") / ("revisao_" + Path(mp4).stem); pasta.mkdir(exist_ok=True)
    quadros = []
    for i, c in enumerate(cenas):
        t1 = cenas[i + 1]["t0"] if i + 1 < len(cenas) else dur
        lin = []
        for f in (0.2, 0.75):
            tt = c["t0"] + (t1 - c["t0"]) * f; arq = pasta / "_q.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{tt:.2f}", "-i", str(mp4), "-frames:v", "1",
                            "-vf", "scale=400:-2", str(arq)], check=True)
            lin.append(Image.open(arq).copy())
        im = Image.new("RGB", (810, lin[0].height + 22), "black"); im.paste(lin[0], (0, 22)); im.paste(lin[1], (410, 22))
        rot = f"{i} · {int(c['t0'] // 60)}:{c['t0'] % 60:04.1f} · {c['tipo']} · {c['arquivo'][:34]} · {t1 - c['t0']:.1f}s"
        if c.get("kanji"):
            rot += " · " + " ".join(k or "" for k in c["kanji"])
        ImageDraw.Draw(im).text((4, 4), rot, fill="yellow")
        if t1 - c["t0"] < 2.5 and c["tipo"] not in ("vigia",):
            AVISOS.append(f"cena {i} ({rot}) dura só {t1 - c['t0']:.1f}s")
        quadros.append(im)
    for k in range(0, len(quadros), 8):
        g = quadros[k:k + 8]; h = g[0].height
        sh = Image.new("RGB", (810 * 2, h * 4))
        for j, im in enumerate(g):
            sh.paste(im, ((j % 2) * 810, (j // 2) * h))
        sh.save(pasta / f"folha_{k // 8:02d}.jpg", quality=85)
    print(f"{len(cenas)} cenas → folhas em {pasta} (olhar TODAS antes de mandar)")
    # 15/11 (usuário): "silêncio sem motivo parece erro, a pessoa sai do vídeo" — procura trechos > 3 s quase mudos
    import numpy as np
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32)
    j = x[:len(x) // 4000 * 4000].reshape(-1, 4000)                     # janelas de 0,5 s
    db = 20 * np.log10(np.sqrt((j ** 2).mean(1)) + 1e-7)
    mudo, ini = db < -31, None      # sem voz e só um fundo muito baixo (o rascunho do Ep. 09 tinha -35 a -40)
    for k, m in enumerate(list(mudo) + [False]):
        if m and ini is None:
            ini = k
        elif not m and ini is not None:
            if (k - ini) * 0.5 >= 3.5 and ini * 0.5 < dur - 25:           # o fim (tela de inscrição) não conta
                AVISOS.append(f"quase silêncio de {(k - ini) * 0.5:.1f}s em {int(ini * 0.5 // 60)}:{ini * 0.5 % 60:04.1f} — só pode se for o silêncio de um susto")
            ini = None
    longos = sum(1 for k in range(len(db)) if db[k] < -38)
    print(f"trechos de 0,5 s muito baixos (< -38 dB): {longos}")
    if log and Path(log).exists():
        txt = Path(log).read_text()
        for m in re.findall(r"vídeo (\S+): desacelerado para ([0-9.]+)", txt):
            ERROS.append(f"vídeo {m[0]} desacelerado pelo motor ({m[1]}×): vai travar — cena mais curta ou trecho mais longo")
        n = len(re.findall(r"aviso mix", txt))
        if n > 40:
            AVISOS.append(f"{n} avisos de mix (música/efeitos perto da voz) — baixar a trilha")
        for m in re.findall(r"aviso salto: .*", txt):
            AVISOS.append(m)


if __name__ == "__main__":
    a = sys.argv[1:]
    {"voz": voz, "roteiro": roteiro}.get(a[0], lambda: video(*a[1:]))()
    for e in ERROS:
        print("ERRO  ", e)
    for w in AVISOS:
        print("aviso ", w)
    print(f"— {len(ERROS)} erro(s), {len(AVISOS)} aviso(s)")
    sys.exit(1 if ERROS else 0)
