"""28/11 (usuário: "quero o áudio em português nos trechos do filme"): os trechos usam a DUBLAGEM, e a fala amarela
na tela é o que a dublagem diz (não a legenda, que é outra tradução, em outro tempo). Para cada trecho de
cortar_filmes.TRECHOS: transcreve a dublagem (Whisper, palavra a palavra) com folga, alarga o corte para nenhuma
palavra ficar cortada e grava filme/dublagem.json {nome: {"a", "b", "falas": [[t0, t1, texto], ...]}}.
O texto passa por CORRECOES (o que o Whisper erra, conferido ouvindo). Uso: python3 dublagem.py [nome ...]"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf

AQUI = Path(__file__).parent
SAIDA = AQUI / "filme" / "dublagem.json"
src = (AQUI / "cortar_filmes.py").read_text()
TRECHOS = {m[0]: (float(m[1]), float(m[2]), m[3] == "True") for m in
           re.findall(r'"(\w+)":\s*\(([\d.]+),\s*([\d.]+),\s*(True|False)', src)}
FOLGA = 3.0
CORRECOES = {"*": [("Nick", "Nikki"), ("Niki", "Nikki"), ("Nikkii", "Nikki"), ("contrajiga", "contradiga"), ("Baird", "Bear"), ("Bair", "Bear")],
             "p5_telefone": [("Conta aí.", "Quem tá aí?")]}   # nome: [(errado, certo), ...]; "*" vale para todos


# conferido palavra a palavra (Whisper medium com dica de nomes, 28/11): onde a transcrição automática errava
MANUAL = {
    "g_sala": {"a": 3895.0, "b": 3904.36, "falas": [[0.54, 2.41, "Puta merda!"], [5.64, 7.01, "Que aconteceu?"],
                                                   [7.68, 9.01, "Que aconteceu aqui?"]]},
    "s_saidas": {"a": 5572.03, "b": 5586.30, "falas": [[0.35, 4.2, "Bom, talvez, talvez, se uma outra pessoa fizer um"],
                                                     [4.21, 6.9, "desejo que contradiga o seu,"],
                                                     [7.03, 9.0, "pede pra ela, sei lá, já que é pra você,"],
                                                     [9.0, 10.6, "pode ser que ela faça."], [10.97, 12.7, "Ou você podia morrer."],
                                                     [12.75, 14.27, "Quer dizer, você poderia se matar."]]},
    "s_oque": {"a": 6355.4, "b": 6358.3, "falas": [[1.0, 2.55, "O que você fez?"]]},
}
CORTE_FIM = {"s_saidas": (5586.30, "poderia se matar.")}   # termina na frase dele (o resto já é outra fala)


def linhas(palavras, maxc=44):
    """agrupa palavras em falas: quebra em pausa > 0,45 s, ponto final ou linha longa"""
    out, cur = [], []
    for w in palavras:
        if cur and (w[0] - cur[-1][1] > 0.45 or len(" ".join(x[2] for x in cur + [w])) > maxc):
            out.append(cur); cur = []
        cur.append(w)
        if w[2].endswith((".", "?", "!")):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return [[round(c[0][0], 2), round(c[-1][1] + 0.25, 2), " ".join(x[2] for x in c)] for c in out]


def main(nomes):
    from faster_whisper import WhisperModel
    m = WhisperModel("medium", compute_type="int8")
    res = json.loads(SAIDA.read_text()) if SAIDA.exists() else {}
    tmp = Path("/tmp/claude-0/dub.wav")
    for nome in nomes or list(TRECHOS):
        a, b, som = TRECHOS[nome]
        if not som:
            res[nome] = {"a": a, "b": b, "falas": []}; continue
        ini = a - FOLGA
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.3f}", "-t", f"{b - a + 2 * FOLGA:.3f}", "-i",
                        str(AQUI / "filme" / "obsessao.mkv"), "-map", "0:a:0", "-ac", "1", "-ar", "16000", str(tmp)], check=True)
        x, _ = sf.read(tmp, dtype="float32")
        segs, _ = m.transcribe(x, language="pt", word_timestamps=True, vad_filter=False)
        ws = [(ini + w.start, ini + w.end, w.word.strip()) for s in segs for w in s.words if w.word.strip()]
        dentro = [w for w in ws if w[1] > a + 0.15 and w[0] < b - 0.15]
        if dentro:   # a frase da dublagem vai até o fim (e começa do começo): junta as palavras coladas (< 0,6 s)
            i0, i1 = ws.index(dentro[0]), ws.index(dentro[-1])
            fimf = lambda w: w[2].endswith((".", "?", "!", "…"))
            while i1 + 1 < len(ws) and not fimf(ws[i1]) and ws[i1 + 1][0] - ws[i1][1] < 0.6 and ws[i1 + 1][1] < b + 3.0:
                i1 += 1   # só completa a frase que ficou pela metade
            while i0 > 0 and not fimf(ws[i0 - 1]) and ws[i0][0] - ws[i0 - 1][1] < 0.6 and ws[i0 - 1][0] > a - 2.0:
                i0 -= 1
            dentro = ws[i0:i1 + 1]
        na = min([a] + [w[0] - 0.35 for w in dentro]); nb = max([b] + [w[1] + 0.6 for w in dentro])
        for w in ws:   # não puxar meia palavra de fora
            if w not in dentro and w[0] < na < w[1]:
                na = w[1] + 0.05
            if w not in dentro and w[0] < nb < w[1]:
                nb = w[0] - 0.05
        falas = [[round(t0 - na, 2), round(min(t1, nb) - na, 2), txt] for t0, t1, txt in linhas(dentro)]
        for errado, certo in CORRECOES["*"] + CORRECOES.get(nome, []):
            falas = [[p, q, t.replace(errado, certo)] for p, q, t in falas]
        if nome in CORTE_FIM:
            nb, ult = CORTE_FIM[nome]
            falas = [[p, min(q, round(nb - na, 2)), t] for p, q, t in falas if p < nb - na]
            falas[-1][2] = ult
        res[nome] = MANUAL.get(nome) or {"a": round(na, 2), "b": round(nb, 2), "falas": falas}
        print(f"{nome:13s} {a:.2f}-{b:.2f} → {na:.2f}-{nb:.2f}  " + " | ".join(f"{p}:{t}" for p, _, t in falas), flush=True)
        SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
