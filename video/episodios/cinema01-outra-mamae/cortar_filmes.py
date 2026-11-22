"""Cenas do filme Outra Mamãe (2026) → filmes_prontos/<nome>.mp4 (+ <nome>.wav quando tem som original), 21/11.
- O filme (filme/outra_mamae.mkv, fora do git) é 1920×872 a 23,976 q/s; dublagem em português na faixa 0:1.
- Cada trecho tem 3–10 s. Os tempos saem da legenda oficial (filme/legenda_pt.srt): o corte abre ~0,4 s antes da fala
  e fecha ~0,3 s depois.
- som=True (as cenas 🔊 do roteiro): sai também o .wav da DUBLAGEM (o Vigia se cala e o filme fala) e a fala vai
  escrita embaixo do quadro, com o texto da legenda oficial.
- Moldura de arquivo (igual aos filmes do Ep. 11): o quadro no centro, o fundo com ele mesmo desfocado, crédito em cima.
  O filme é escuro: a cor sobe um pouco (gama) em vez de descer; "luz" > 1 clareia mais os planos muito escuros.
- A taxa fica a original: o motor passa pelo RIFE e chega a 30 q/s sem tranco.
Uso: python3 cortar_filmes.py [nome ...]"""
import json, re, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent
FILME = AQUI / "filme" / "outra_mamae.mkv"
SAI = AQUI / "filmes_prontos"; SAI.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONTE_FALA = "/usr/share/fonts/opentype/inter/Inter-SemiBoldItalic.otf"   # 22/11: fala do filme ≠ legenda da narração
CREDITO = "OUTRA MAMÃE (2026) · DIR. ROB SAVAGE · UNIVERSAL PICTURES"

# nome: (início, fim, som, luz)   — tempos em segundos do filme
TRECHOS = {
    "g_boanoite":   (148.6, 155.0, True, 1.5),   # 02:32 "Boa noite, Outra Mamãe."
    "g_coracao":    (602.1, 605.0, True, 1.0),    # 10:02 "Posso entrar no seu coração?"
    "p1_coracao":   (1716.8, 1721.3, True, 1.0),  # 28:38 "Bela, por favor, me deixe entrar no seu coração."
    "p1_medium":    (3590.9, 3594.0, True, 1.0),  # 59:51 "…mas precisam de permissão para existir."
    "p2_almoco":    (462.4, 469.4, False, 1.0),   # 07:42 a "mãe" que volta para almoçar
    "p2_kelvin":    (1623.4, 1633.1, True, 1.0),  # 27:03 "Não sabia que podia ser o Kelvin também" / "Vou ser quem você quiser"
    "p3_grande":    (860.6, 867.0, False, 1.0),   # 14:23 "ficar bem grande, ficar bem pequena"
    "p4_segredos":  (356.4, 363.2, False, 1.0),   # 06:00 "Mesmo time."
    "p5_frank":     (2381.9, 2387.7, True, 1.45), # 39:42 "Pode fazer o tio Frank ir embora?" / "É uma ótima ideia."
    "p6_pessoa":    (2355.5, 2359.0, True, 1.45),  # 39:15 "Não me permitiram ser uma pessoa."
    "p6_existir":   (1721.8, 1725.4, True, 1.0),  # 28:42 "Dói muito, Bela. Eu preciso existir."
    "p7_trocar":    (2705.6, 2708.8, True, 1.0),  # 45:06 "Ela quer trocar de lugar comigo."
    "p7_eu":        (3017.3, 3020.9, True, 1.0),  # 50:17 "Eu vou ser você e você será eu."
    "caso_cheiro":  (909.5, 919.4, True, 1.0),    # 15:09 "Você está com o cheiro de outra pessoa." … "Sou a Mamãe."
    "t3_ardiloso":  (3561.3, 3566.8, True, 1.0),  # 59:21 "Um ser ardiloso…"
    "t3_ritual":    (3690.5, 3697.0, False, 1.1), # 61:30 o ritual visto de cima (vela, água e sal)
    "t4_imaginaria": (823.3, 833.7, False, 1.0),  # 13:43 "não é uma amiga imaginária?" … "muito boa em se esconder"
    "capgras":      (1785.2, 1787.7, True, 1.0),  # 29:45 "É você mesmo?"
    "s_afundou":    (3078.8, 3084.5, False, 1.0), # 51:19 "Aquilo afundou com ela."
    "s_mar":        (3138.2, 3141.6, True, 1.0),  # 52:18 "Bela, vamos ver o mar?"
    "s_ruth":       (3453.4, 3460.0, False, 1.0), # 57:33 a avó Ruth
    "s_inocencia":  (3593.4, 3597.7, True, 1.0),  # 59:53 "Quando a inocência da Bela for quebrada, o demônio não vai querer mais ela."
    "s_confissao":  (4445.0, 4452.0, False, 1.0), # 74:05 a confissão de Ursula
    "s_sim":        (4659.4, 4665.4, True, 1.0),  # 77:39 "Eu vou dizer sim. Por favor!" / "Estou pronta."
    "s_avo":        (4782.7, 4788.0, False, 1.0), # 79:43 a voz da avó
    "s_nao":        (4809.6, 4817.6, True, 1.0),  # 80:09 "Mas eu sou mentirosa como eles. Eu não quero você! Eu escolho não!"
    "s_pensar":     (4884.9, 4889.8, True, 1.0),  # 81:25 "Toda vez que olhar para ela, você vai pensar em mim."
    "s_escola":     (5077.8, 5085.0, False, 1.0), # 84:38 "Todos sobreviveram."
    "pos_creditos": (5575.1, 5583.0, False, 1.8), # 92:55 depois dos créditos: a Outra Mamãe no escuro
    "abertura":     (39.4, 52.4, False, 1.0),     # 00:39 a frase de abertura na tela
    # 22/11 (rascunho 2): CENAS QUE ROLAM sob a narração (sem som; o canal de análise sempre tem filme passando)
    "b_bela_cama":   (118.0, 134.0, False, 1.4),   # 01:58 Bela na cama, a câmera chega perto
    "b_familia":     (72.0, 92.0, False, 1.0),     # 01:12 a família brincando
    "b_outra_rosto": (592.5, 612.0, False, 1.0),   # 09:52 o rosto da Outra Mamãe
    "b_cozinha":     (476.0, 498.0, False, 1.0),   # 07:56 a "mãe" na cozinha, na hora do almoço
    "b_mesa":        (699.0, 707.5, False, 1.0),   # 11:39 a coisa se dobrando debaixo da mesa
    "b_quarto_portas": (836.0, 856.0, False, 1.25),# 13:56 "ela mora atrás das nossas portas"
    "b_pai_sofa":    (366.0, 386.0, False, 1.0),   # 06:06 o pai no sofá
    "b_bela_sozinha": (384.0, 408.0, False, 1.0),  # 06:24 Bela sozinha com a maquete
    "b_pais_briga":  (756.0, 786.0, False, 1.35),  # 12:36 os pais discutindo à noite
    "b_porta_azul":  (1773.0, 1783.0, False, 1.45),# 29:33 a Outra Mamãe na porta
    "b_outro_lado":  (1661.0, 1690.0, False, 1.1), # 27:41 o mundo de cabeça para baixo
    "b_frank_fim":   (2470.0, 2490.0, False, 1.5), # 41:10 o que sobrou do tio Frank
    "b_abraco":      (2338.0, 2355.0, False, 1.7), # 38:58 a criatura abraça Bela no banheiro
    "b_praca":       (2724.0, 2752.0, False, 1.0), # 45:24 a família em crise na praça de alimentação
    "b_tunel":       (2955.0, 2978.0, False, 1.2), # 49:15 o túnel vermelho do parquinho
    "b_bolinhas":    (3028.0, 3050.0, False, 1.0), # 50:28 o chão de bolinhas engole a menina
    "b_quarto_bolas": (3106.0, 3128.0, False, 1.0),# 51:46 o quarto vira mar de bolinhas
    "b_mar":         (3143.0, 3162.0, False, 1.0), # 52:23 o mar
    "b_carro_outra": (3214.0, 3236.0, False, 1.0), # 53:34 a Outra Mamãe de amarelo, no carro
    "b_avo":         (3418.0, 3448.0, False, 1.3), # 56:58 a avó Ruth à luz da lamparina
    "b_medium":      (3538.0, 3558.0, False, 1.0), # 58:58 a médium Lois
    "b_ritual_sal":  (3779.0, 3797.0, False, 1.2), # 63:00 a vela e o coração de sal
    "b_uv":          (3822.0, 3852.0, False, 1.0), # 63:42 o ritual dá errado
    "b_espelho":     (4170.0, 4196.0, False, 1.2), # 69:30 o sorriso no espelho
    "b_maos_porta":  (4425.0, 4436.0, False, 1.5), # 73:45 as mãos na porta
    "b_cicatriz":    (4458.0, 4480.0, False, 1.15),# 74:18 a mãe marcada
    "b_rasteja":     (4836.0, 4858.0, False, 1.6), # 80:36 a coisa rastejando no banheiro
    "b_rosto_final": (4895.0, 4916.0, False, 1.35),# 81:35 o rosto da criatura de perto
    "b_familia_fim": (4944.0, 4968.0, False, 1.15),# 82:24 a família de novo
    "b_creditos":    (5470.0, 5476.0, False, 1.0), # 91:10 os créditos subindo
}
CAUDA = 12.0   # 22/11: depois da fala, o filme CONTINUA rolando (sem som) sob a narração — nada de quadro congelado


def legenda():
    s = (AQUI / "filme" / "legenda_pt.srt").read_text(encoding="utf-8")
    out = []
    for b in s.strip().split("\n\n"):
        l = b.splitlines()
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", l[1]) if len(l) > 2 else None
        if m:
            g = list(map(int, m.groups()))
            out.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000,
                        " ".join(x.strip().lstrip("-").strip() for x in l[2:])))
    return out


def esc(t):
    return t.replace("\\", "\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\%").replace(",", "\\,")


LEG = legenda()
info = {}
fw, fh = 1600, 727; fx, fy = (1920 - fw) // 2, 150          # 2,2:1 do filme
for nome in sys.argv[1:] or list(TRECHOS):
    a, b, som, luz = TRECHOS[nome]
    fim_v = b + (CAUDA if som else 0.0)   # o vídeo vai além da fala; o som (.wav) é só a fala
    cor = f"eq=gamma={1.12 * luz:.2f}:brightness={0.015 * luz:.3f}:saturation=0.85:contrast=1.04,noise=alls=6:allf=t"
    falas = [(max(0, x - a), min(b - a, y - a), t) for x, y, t in LEG
             if min(y, b) - max(x, a) > 0.6 * (y - x)] if som else []   # só a fala que cabe (quase) inteira no trecho
    # 22/11: a fala do filme fica DENTRO do quadro, amarela, em itálico e com tarja — não se confunde com a legenda
    # da narração (que é branca, embaixo da tela)
    txt = "".join(f",drawtext=fontfile={FONTE_FALA}:text='{esc(t)}':fontsize=42:fontcolor=0xffd75e:box=1:boxcolor=0x000000@0.62"
                  f":boxborderw=14:x=(w-text_w)/2:y={fy + fh - 96}:enable='between(t,{x:.2f},{y:.2f})'" for x, y, t in falas)
    fc = (f"[0:v]setpts=PTS-STARTPTS,{cor},split[a][b];"
          f"[a]scale=480:218,boxblur=12:3,eq=brightness=-0.22:saturation=0.6,scale=1920:1080[fundo];"
          f"[b]scale={fw}:{fh},pad={fw + 4}:{fh + 4}:2:2:color=0xb8b0a4@0.55[quadro];"
          f"[fundo][quadro]overlay={fx - 2}:{fy - 2},"
          f"drawtext=fontfile={FONTE}:text='TRECHO DE FILME':fontsize=22:fontcolor=0xc8302c:x={fx}:y={fy - 46},"
          f"drawtext=fontfile={FONTE}:text='{esc(CREDITO)}':fontsize=22:fontcolor=0xd8d0c4:x={fx + 230}:y={fy - 46}{txt},format=yuv420p[v]")
    saida = SAI / f"{nome}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{fim_v - a:.3f}", "-i", str(FILME), "-filter_complex", fc,
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "19", "-preset", "medium", str(saida)], check=True)
    if som:   # a dublagem, com entrada e saída suaves
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(FILME), "-map", "0:1",
                        "-af", f"afade=t=in:d=0.25,afade=t=out:st={b - a - 0.35:.2f}:d=0.35", "-ar", "48000", "-ac", "2",
                        str(SAI / f"{nome}.wav")], check=True)
    info[nome] = {"dur": round(b - a, 2), "video_dur": round(fim_v - a, 2), "som": som, "falas": [[round(x, 2), round(y, 2), t] for x, y, t in falas]}
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida), "-vf", f"fps=1/{max(0.5, (fim_v - a) / 6):.2f},scale=320:-2,tile=6x1",
                    "-frames:v", "1", str(SAI / f"{nome}_conferir.jpg")], check=True)
    print(f"ok {nome}: {b - a:.1f}s {'🔊 ' + ' | '.join(t for _, _, t in falas) if som else ''}", flush=True)
arq = SAI / "trechos.json"
antigo = json.loads(arq.read_text()) if arq.exists() else {}
arq.write_text(json.dumps({**antigo, **info}, ensure_ascii=False, indent=1))
