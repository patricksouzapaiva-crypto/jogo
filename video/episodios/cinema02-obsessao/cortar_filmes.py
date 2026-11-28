"""Cenas do filme Obsessão (2026) → filmes_prontos/<nome>.mp4 (+ <nome>.wav da dublagem), 27/11.
Cópia do cortar_filmes.py do #1, com as regras novas:
- Content ID (lição do #1, bloqueado pela NBC por ~6 min de filme DE FUNDO): o filme entra SÓ nos trechos das falas-pista,
  curtos, para comentário. Nada de filme rolando atrás da narração.
- O filme inteiro não cabe no disco nem na memória: os trechos usados foram copiados sem recodificar para
  filme/trechos/t_<s>.mkv (início real de cada um em filme/trechos/inicios.json). Este script lê de lá.
- 27/11 (usuário: "cadência nas trocas, nada de corte seco"): todo trecho nasce do preto e volta ao preto (fade de
  0,35 s na imagem) e a dublagem sobe e desce em fade. Saída sempre H.264 yuv420p.
- Moldura de arquivo (igual ao #1): o quadro no centro, o fundo com ele mesmo desfocado, crédito em cima, e a fala do
  filme em amarelo itálico dentro do quadro (não se confunde com a legenda da narração).
Uso: python3 cortar_filmes.py [nome ...]"""
import json, os, re, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent
TR = AQUI / "filme" / "trechos"
INI = json.loads((TR / "inicios.json").read_text())
SAI = AQUI / "filmes_prontos"; SAI.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTE_FALA = "/usr/share/fonts/opentype/inter/Inter-SemiBoldItalic.otf"
CREDITO = "OBSESSÃO (2026) · DIR. CURRY BARKER"
CROP = "crop=1620:1080:150:0"          # o filme vem com faixas pretas dos lados (1,5:1 dentro do 16:9)

# nome: (início, fim, som, luz) em segundos do filme
TRECHOS = {
    "g_sorriso":    (6200.0, 6204.0, True, 1.2),   # 1:43:20 a Nikki ensanguentada, sorrindo (abre o vídeo; 28/11: com o som da cena, nunca mudo)
    "g_sala":       (3895.0, 3904.0, True, 1.0),   # 1:04:55 a Nikki de pé no meio da sala, molhada; "Cacete!"
    "g_espera":     (3921.6, 3926.0, True, 1.0),   # 1:05:21 "Eu só estava esperando você chegar."
    "g_desejo":     (1236.0, 1242.6, True, 1.4),   # 0:20:36 "Desejo ser a pessoa que Nikki Freeman mais ama no mundo."
    "p1_caixa":     (597.0, 603.2, False, 1.0),    # 0:09:57 a caixa: "VOCÊ SÓ TEM DIREITO A UM DESEJO"
    "p1_morrer":    (3818.6, 3822.8, True, 1.0),   # 1:03:38 "Quando você morrer, o desejo desaparece."
    "p3_carro":     (1408.4, 1411.6, True, 1.2),   # 0:23:28 "Nikki, não. Por que está entrando no meu carro?"
    "p3_horas":     (4086.6, 4089.4, True, 1.0),   # 1:08:06 "Não consegue ficar sem ela por três horas?"
    "p4_festa":     (4365.6, 4373.6, True, 1.0),   # 1:12:45 "E todo mundo aqui vai morrer…"
    "p5_telefone":  (3856.2, 3872.4, True, 1.0),   # 1:04:16 "Quer falar com ela?" … "A Nikki." … o grito
    "p5_madrugada": (5004.7, 5016.6, True, 1.4),   # 1:23:24 "Me mata, por favor." … "Ela está dormindo." "Sou eu."
    "p6_escolheu":  (3776.6, 3784.8, True, 1.0),   # 1:02:56 "O amor dela é verdadeiro?" "Ter escolhido isso pra ela…"
    "s_culpa":      (5333.5, 5339.6, True, 1.2),   # 1:28:53 "Isso tudo é culpa sua… Você desejou isso."
    "s_saidas":     (5572.3, 5585.8, True, 1.0),   # 1:32:52 "…um pedido que seja o oposto do seu…" "Ou você poderia morrer."
    "s_sempre":     (5945.5, 5952.6, True, 1.2),   # 1:39:05 "A gente vai ficar junto pra sempre…"
    "s_galho":      (6154.8, 6161.0, True, 1.0),   # 1:42:35 a melodia da caixa e o estalo do galho
    "s_abraco":     (6215.0, 6223.0, False, 1.2),  # 1:43:35 o abraço (sem som)
    "s_volta":      (6296.0, 6305.0, True, 1.3),   # 1:44:56 a Nikki para de chorar e olha em volta
    "s_oque":       (6355.4, 6358.8, True, 1.3),   # 1:45:55 "O que você fez?"
}
FADE = 0.35
CAUDA = 0.5    # 28/11 (rascunho 1: "começa no meio da palavra"): o trecho segue 0,5 s depois da última fala
# 28/11 (rascunho 2: "quero o áudio em português" + "trocas suaves, quase imperceptíveis"): a DUBLAGEM volta, e o corte
# e a fala amarela saem dela (filme/dublagem.json, feito por dublagem.py) — não da legenda, que é outra tradução em
# outro tempo. Sem escurecer até o preto: a troca de cena é uma fusão feita pelo montador.
DUB = json.loads((AQUI / "filme" / "dublagem.json").read_text()) if (AQUI / "filme" / "dublagem.json").exists() else {}
FADE_PRETO = 0.0


def fonte(a):
    """o arquivo de trecho que contém o instante a (e o início real dele)"""
    cands = [(k, f) for f, k in INI.items() if k <= a + 0.01 and (TR / f).exists()]
    k, f = max(cands)
    return TR / f, k


def legenda():
    s = (AQUI / "filme" / "legenda_pt.srt").read_text(encoding="utf-8-sig")
    out = []
    for b in s.strip().split("\n\n"):
        l = b.splitlines()
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", l[1]) if len(l) > 2 else None
        if m:
            g = list(map(int, m.groups()))
            out.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000,
                        " ".join(re.sub(r"</?i>", "", x).strip().lstrip("-").strip() for x in l[2:])))
    return out


def esc(t):
    return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%").replace(",", "\\,")


LEG = legenda()
arq_info = SAI / "trechos.json"
info = json.loads(arq_info.read_text()) if arq_info.exists() else {}
fw, fh = 1440, 960; fx, fy = (1920 - fw) // 2, 80
for nome in sys.argv[1:] or list(TRECHOS):
    a, b, som, luz = TRECHOS[nome]
    if nome in DUB:
        a, b = DUB[nome]["a"], DUB[nome]["b"]
    src, k0 = fonte(a); off = a - k0; d = b - a + (0 if nome in DUB else CAUDA if som else 0)
    cor = f"eq=gamma={1.08 * luz:.2f}:brightness={0.012 * luz:.3f}:saturation=0.88:contrast=1.04,noise=alls=5:allf=t"
    if nome in DUB:
        falas, ant = [], "."
        for x, y, t in (DUB[nome]["falas"] if som else []):   # maiúscula só no começo de frase
            t = t.replace("O que?", "O quê?")
            falas.append((x, y, t[:1].upper() + t[1:] if ant.endswith((".", "?", "!", "…")) else t)); ant = t
    else:
        falas = [(max(0, x - a), min(d, y - a), t) for x, y, t in LEG if min(y, b) - max(x, a) > 0.6 * (y - x)] if som else []
    txt = "".join(f",drawtext=fontfile={FONTE_FALA}:text='{esc(t)}':fontsize=40:fontcolor=0xffd75e:box=1:boxcolor=0x000000@0.62"
                  f":boxborderw=14:x=(w-text_w)/2:y={fy + fh - 92}:enable='between(t,{x:.2f},{y:.2f})'" for x, y, t in falas)
    fc = (f"[0:v]setpts=PTS-STARTPTS,{CROP},{cor},split[a][b];"
          f"[a]scale=480:320,boxblur=12:3,eq=brightness=-0.24:saturation=0.6,scale=1920:1080,setsar=1[fundo];"
          f"[b]scale={fw}:{fh},pad={fw + 4}:{fh + 4}:2:2:color=0xb8b0a4@0.55[quadro];"
          f"[fundo][quadro]overlay={fx - 2}:{fy - 2},"
          f"drawtext=fontfile={FONTE}:text='TRECHO DE FILME':fontsize=22:fontcolor=0xc8302c:x={fx}:y={fy - 42},"
          f"drawtext=fontfile={FONTE}:text='{esc(CREDITO)}':fontsize=22:fontcolor=0xd8d0c4:x={fx + 230}:y={fy - 42}{txt},"
          + (f"fade=t=in:d={FADE_PRETO},fade=t=out:st={d - FADE_PRETO:.2f}:d={FADE_PRETO}," if FADE_PRETO else "")
          + "fps=24,format=yuv420p[v]")
    saida = SAI / f"{nome}.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{off:.3f}", "-t", f"{d:.3f}", "-i", str(src),
                    "-filter_complex", fc.replace("[0:v]", "[0:v:0]"), "-map", "[v]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "medium", str(saida)], check=True)
    if som:   # 28/11: o ÁUDIO ORIGINAL (inglês, faixa 2) — a legenda pt é tradução dele; a dublagem dizia outra coisa,
              # em outro tempo (rascunho 1: "as cenas não coincidem com a fala", corte no meio da palavra)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{off:.3f}", "-t", f"{d:.3f}", "-i", str(src), "-map", "0:a:0",
                        "-af", f"pan=stereo|FL=FC+0.45*FL+0.3*BL+0.3*SL|FR=FC+0.45*FR+0.3*BR+0.3*SR,loudnorm=I=-18:TP=-2:LRA=11,"
                        f"afade=t=in:d=0.4,afade=t=out:st={d - 0.6:.2f}:d=0.6", "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2",
                        str(SAI / f"{nome}.wav")], check=True)
    info[nome] = {"dur": round(d, 2), "video_dur": round(d, 2), "som": som, "falas": [[round(x, 2), round(y, 2), t] for x, y, t in falas]}
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(saida), "-vf", f"fps=1/{max(0.5, d / 6):.2f},scale=320:-2,tile=6x1",
                    "-frames:v", "1", str(SAI / f"{nome}_conferir.jpg")], check=True)
    print(f"ok {nome}: {d:.1f}s {'🔊 ' + ' | '.join(t for _, _, t in falas) if som else ''}", flush=True)
    arq_info.write_text(json.dumps(info, ensure_ascii=False, indent=1))
