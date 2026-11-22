"""22/11 (usuário: "a voz ainda continua diferente naqueles quadros e naquelas vozes novas"): regrava TODAS as falas que
foram geradas depois da narração principal do jeito que a principal foi feita — com as 3 frases anteriores do roteiro
na frente (o TTS pega o mesmo tom e ritmo; o contexto é cortado fora pelo Whisper) e com a mesma limpeza (afftdn).
- falas dentro da narração (a da "nona prova", o início do duplo e a introdução das fadas) → voltam para a trilha
  audio/voz_com_vinheta_limpa.wav no lugar das antigas (backup em audio/voz_r5.wav);
- falas lidas nas fichas (spoiler, livro × filme, os "parentes") → audio/extras/*.wav.
Depois: python3 alinhar.py.  Uso: python3 refazer_vozes.py (os brutos do TTS ficam em audio/extras/ctx_*.wav)"""
import importlib, os, re, shutil, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "painel"))
from gerar import tokens  # noqa: E402
import falas as F

AQUI = Path(__file__).parent; A = AQUI / "audio"; X = A / "extras"
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
LIMPA = "afftdn=nr=12:nf=-50"   # a mesma limpeza da narração principal (narrar.py)
SR = 48000
CTX = int(os.environ.get("CTX", 12))   # 22/11: com só 3 frases o TTS lia mais devagar e mais "teatral" que a narração (medido: 2,5 × 3,8 pal/s)
src = (AQUI / "narrar.py").read_text()
ns = {"__file__": str(AQUI / "narrar.py"), "__name__": "narrar_funcs"}
ns.update(re=re, subprocess=subprocess, np=np, unicodedata=__import__("unicodedata"), _modelo=None)
exec(src[src.index("norm = lambda"):src.index("\n", src.index("norm = lambda"))], ns)
exec(src[src.index("def palavras"):src.index("def texto")], ns)   # só as funções; o resto do narrar.py não roda
palavras, achar, norm = ns["palavras"], ns["achar"], ns["norm"]

novo, sec, direc, _ = F.ler(); novo = novo + [F.VINHETA]
velho = list(novo)   # a trilha atual já segue o ROTEIRO.md (alinhamento.json atual); só os pedaços refeitos mudam
SO = set(filter(None, os.environ.get("SO", "").split(",")))   # SO=parentes,livro: refaz só esses (teste)
QUEBRAS = set(sec.values()) | set(direc)
I = lambda c: next(i for i, f in enumerate(novo) if f.startswith(c))
tts_txt = lambda f: F.para_tts(f).strip()


def ler(w):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(w), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                                        capture_output=True, check=True).stdout, np.int16)


def gravar(a, w):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(w)], input=a.tobytes(), check=True)


def tts(texto, bruto):
    if bruto.exists():
        return
    t = bruto.with_suffix(".txt"); t.write_text(texto + "\n")
    for _ in range(4):
        r = subprocess.run([sys.executable, str(FERR), str(t), str(bruto)], env={**os.environ, "VOZ": "Algenib"})
        if r.returncode == 0 and bruto.exists():
            return
        __import__("time").sleep(30)
    sys.exit(f"TTS falhou: {bruto.name}")


def gerar_com_contexto(nome, i_ctx, partes):
    """partes = textos novos (cada um vira um pedaço); devolve [áudio de cada parte] já limpo, a 48 kHz."""
    ctx = ""
    for i in range(i_ctx - CTX, i_ctx):   # o contexto com os mesmos parágrafos da narração principal
        ctx += ("" if i == i_ctx - CTX else ("\n\n" if i in QUEBRAS else " ")) + tts_txt(novo[i])
    bruto = X / f"ctx_{nome}.wav"
    corpo = ""
    for j, p in enumerate(partes):   # p = texto, ou (texto, parágrafo_novo): respiro maior só onde o roteiro tem seção/cena
        t, quebra = (p, True) if isinstance(p, str) else p
        corpo += ("" if j == 0 else ("\n\n" if quebra else " ")) + tts_txt(t)
    tts(ctx + "\n\n" + corpo, bruto)
    limpo = X / f"ctx_{nome}_limpo.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(bruto), "-af", LIMPA, "-ar", str(SR), "-ac", "1", str(limpo)], check=True)
    a = ler(limpo); ws = palavras(bruto)
    inis, p0 = [], 1
    for p in partes:
        alvo = tts_txt(p if isinstance(p, str) else p[0])
        sub = ws[p0 - 1:]; k = achar(sub, alvo)
        if k is None:
            sys.exit(f"{nome}: não achei '{alvo[:40]}' em: {' '.join(w[0] for w in sub[:60])}")
        k += p0 - 1; inis.append(k); p0 = k + 2
    cortes = [(ws[k - 1][2] + ws[k][1]) / 2 for k in inis] + [min(len(a) / SR, ws[-1][2] + 0.45)]
    out = []
    for j in range(len(partes)):
        s = a[int(cortes[j] * SR):int(cortes[j + 1] * SR)].astype(np.float32)
        n = int(0.03 * SR); s[:n] *= np.linspace(0, 1, n)
        if j == len(partes) - 1:
            n = int(0.12 * SR); s[-n:] *= np.linspace(1, 0, n)
        out.append(s.astype(np.int16))
        print(f"  {nome} [{j}] {len(s) / SR:5.2f}s  {(p if isinstance(p, str) else p[0])[:60]}")
    return out


# ---- 1) trilha da narração: segmentos atuais por fala (cortes no meio das pausas)
import json
V = ler(A / "voz_com_vinheta_limpa.wav"); ali = json.load(open(A / "alinhamento.json"))
k = 0; ini, fim = [], []
for f in velho:
    n = len(tokens(f)); ini.append(ali[k][0]); fim.append(ali[k + n - 1][1]); k += n
cv = [0.0] + [(fim[i - 1] + ini[i]) / 2 for i in range(1, len(velho))] + [len(V) / SR]
seg = {}
for i, f in enumerate(velho):
    seg.setdefault(f, []).append(V[int(cv[i] * SR):int(cv[i + 1] * SR)])

# ---- 2) as falas refeitas dentro da narração
refeitas = {}
g1 = list(range(I("Toda teoria vai ter que explicar"), I("O fetch é o duplo")))
g2 = list(range(I("E agora, a última teoria"), I("Na Irlanda, na Escócia e na Escandinávia")))
for nome, g in (("duplo", g1), ("fadas", g2)):
    if SO and nome not in SO:
        continue
    # cada fala é um pedaço; parágrafo novo onde o roteiro tem seção/cena (como no narrar.py)
    for j, a in zip(g, gerar_com_contexto(nome, g[0], [(novo[i], i in QUEBRAS) for i in g])):
        refeitas[j] = a
saida = []
for i, f in enumerate(novo):
    if i in refeitas:
        a = refeitas[i]
        saida.append(a)
    else:
        saida.append(seg[f].pop(0))
if refeitas:
    if not (A / "voz_r5.wav").exists():
        shutil.copy(A / "voz_com_vinheta_limpa.wav", A / "voz_r5.wav")
    gravar(np.concatenate(saida), A / "voz_com_vinheta_limpa.wav")
    print("narração:", round(sum(len(x) for x in saida) / SR, 1), "s")

# ---- 3) as falas das fichas (lidas numa pausa da narração)
EXTRAS = {
    "parentes": (I("Em mil oitocentos e oitenta e dois"),
                 ["Antes da última teoria, duas paradas. Não são teorias: são parentes da Outra Mamãe. O primeiro vem da literatura."]),
    "parentes2": (I("Em mil novecentos e vinte e três"), ["O segundo parente vem da medicina."]),
    "livro": (I("Dois finais opostos"), ["No livro, a criatura vence. No filme, a menina vence."]),
    "spoiler": (I("No meio do filme"), ["Atenção: a partir daqui, spoiler do final. Se você ainda não viu o filme, pula para o tempo que está na tela."]),
}
for nome, (i, txt) in EXTRAS.items():
    if SO and nome not in SO:
        continue
    a, = gerar_com_contexto(nome, i, txt)
    destino = {"parentes": "parentes_1", "parentes2": "parentes_2", "livro": "livro_filme", "spoiler": "spoiler"}[nome]
    gravar(a, X / f"{destino}.wav")
if not SO or "spoiler" in SO:
    gravar(np.concatenate([np.zeros(SR, np.int16), ler(X / "spoiler.wav")]), X / "spoiler_1s.wav")
print("ok")
