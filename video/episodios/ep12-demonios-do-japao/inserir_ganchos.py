"""Ep. 12 (25/11, pedido do usuário): "quando acaba o capítulo o corte para o próximo é muito seco… temos que ter uma
transição mais suave e até ter um gancho, por exemplo antes do capítulo do oni que virou deus… poderia até falar que um
oni pode até virar um deus, e aí entraria o cartão do capítulo dele".

Grava SÓ as frases-gancho novas com a mesma voz (Algenib; o TTS recebe a frase anterior como contexto e o Whisper acha
onde o texto novo começa) e encaixa cada uma logo depois do fim da última fala do capítulo. Insere de trás pra frente,
assim os tempos do alinhamento antigo continuam valendo. O texto da fala no ROTEIRO.md ganha o gancho no fim (o índice
das falas não muda). Depois: alinhar.py.
Uso: python3 inserir_ganchos.py"""
import json, os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np, soundfile as sf

AQUI = Path(__file__).parent; A = AQUI / "audio"
FERR = AQUI.parents[1] / "painel" / "ferramentas" / "narrar_fluxo.py"
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())

# (fala, texto no roteiro, texto falado pelo TTS, 2 primeiras palavras do gancho como o Whisper ouve)
GANCHOS = [
    (27, "E a primeira… foi uma mulher.", "E a primeira… foi uma mulher.", ["e", "a", "primeira"]),
    (50, "Mas todo oni vem de algum lugar. E entra… por uma porta.", "Mas todo ôni vem de algum lugar. E entra… por uma porta.", ["mas", "todo"]),
    (93, "E, às vezes… pode até virar um deus.", "E, às vezes… pode até virar um deus.", ["e", "as", "vezes"]),
    (108, "Porque, com um yokai, ser educado nem sempre basta.", "Porque, com um iôcai, ser educado nem sempre basta.", ["porque", "com"]),
    (145, "E, se saiu… talvez não esteja sozinha.", "E, se saiu… talvez não esteja sozinha.", ["e", "se", "saiu"]),
    (159, "Como nesta história. Que aconteceu… há pouco tempo.", "Como nesta história. Que aconteceu… há pouco tempo.", ["como", "nesta"]),
]
PAUSA = 0.6


def palavras(wav):
    from faster_whisper import WhisperModel
    m = WhisperModel("small", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    seg, _ = m.transcribe(np.frombuffer(raw, np.float32), language="pt", word_timestamps=True)
    return [(norm(w.word).strip(), w.start, w.end) for s in seg for w in s.words]


def gravar(n, contexto, novo, inicio):
    bruto = A / f"gancho_{n}_bruto.wav"
    if not bruto.exists():
        (A / f"gancho_{n}.txt").write_text(contexto + "\n\n" + novo + "\n")
        subprocess.run([sys.executable, str(FERR), str(A / f"gancho_{n}.txt"), str(bruto)],
                       env={**os.environ, "VOZ": "Algenib"}, check=True)
    ws = palavras(bruto)
    k = next((i for i in range(1, len(ws)) if [w[0] for w in ws[i:i + len(inicio)]] == inicio), None)
    if k is None:
        sys.exit(f"gancho {n}: não achei {inicio} em: {' '.join(w[0] for w in ws)}")
    print(f"gancho {n} ouvido:", " ".join(w[0] for w in ws[k:]))
    x, sr = sf.read(bruto, dtype="float32")
    x = x.mean(1) if x.ndim > 1 else x
    c0 = (ws[k - 1][2] + ws[k][1]) / 2; c1 = ws[-1][2] + 0.35
    tmp = A / "_g.wav"; seg48 = A / "_g48.wav"
    sf.write(tmp, x[int(c0 * sr):int(c1 * sr)], sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-af",
                    "afftdn=nr=12:nf=-50,afade=t=in:d=0.02,areverse,afade=t=in:d=0.08,areverse",
                    "-ar", "48000", "-ac", "1", str(seg48)], check=True)
    y, _ = sf.read(seg48, dtype="float32"); tmp.unlink(); seg48.unlink()
    return y


def main():
    sys.path.insert(0, str(AQUI.parents[1] / "painel"))
    import falas as F
    from gerar import tokens
    fl = F.ler()[0]
    ali = json.load(open(A / "alinhamento.json"))
    voz_arq = A / "voz_com_vinheta_limpa.wav"
    copia = Path("/dev/shm/ep12_voz_antes_ganchos.wav")
    if not copia.exists():
        shutil.copy(voz_arq, copia)
    voz, sr = sf.read(voz_arq, dtype="float32")
    v = voz if voz.ndim == 1 else voz.mean(1)
    rms = lambda a: np.sqrt(np.mean(a[np.abs(a) > 0.02] ** 2)) if np.any(np.abs(a) > 0.02) else 1e-3
    roteiro = (AQUI / "ROTEIRO.md").read_text()
    for n, txt, tts, inicio in sorted(GANCHOS, reverse=True):
        if txt in fl[n]:
            print(f"gancho {n}: já está no roteiro, pulando"); continue
        y = gravar(n, fl[n - 1] + " " + fl[n], tts, inicio)
        fim = ali[sum(len(tokens(f)) for f in fl[:n + 1]) - 1][1]
        ini_prox = ali[sum(len(tokens(f)) for f in fl[:n + 1])][0]
        corte = fim + min(0.35, (ini_prox - fim) / 2)
        viz = v[int((corte - 8) * sr):int((corte + 1) * sr)]
        y *= rms(viz) / rms(y)
        ins = np.concatenate([np.zeros(int(PAUSA * sr), np.float32), y, np.zeros(int(0.25 * sr), np.float32)])
        if voz.ndim > 1:
            ins = np.stack([ins] * voz.shape[1], 1)
        i = int(corte * sr)
        voz = np.concatenate([voz[:i], ins, voz[i:]]); v = voz if voz.ndim == 1 else voz.mean(1)
        linha = fl[n]
        assert roteiro.count("\n" + linha + "\n") == 1, f"fala {n} não é uma linha única do ROTEIRO.md"
        roteiro = roteiro.replace("\n" + linha + "\n", "\n" + linha + " " + txt + "\n")
        print(f"gancho {n} inserido em {corte:.2f}s ({len(ins) / sr:.1f}s)")
    sf.write(voz_arq, voz, sr)
    (AQUI / "ROTEIRO.md").write_text(roteiro)


if __name__ == "__main__":
    main()
