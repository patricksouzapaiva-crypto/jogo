"""Alinhamento FORÇADO ao texto do roteiro (16/11, pesquisa do motor — a ideia do WhisperX/stable-ts).
O Whisper dá o tempo APROXIMADO de cada frase; aqui um modelo de letras em português (wav2vec2 XLSR-53 PT, ONNX q4,
~240 MB, CPU) ouve a janela da frase e encaixa o TEXTO EXATO do roteiro, letra por letra (Viterbi CTC). Resultado: o
início e o fim de cada palavra com ~20 ms de resolução — sem depender do que o Whisper "entendeu" (números, nomes
estrangeiros, "tá"/"está" das vozes de personagem).
Uso (biblioteca): forcar(wav, palavras, tempos, grupos) → tempos novos (mesmo formato [(ini, fim), ...]).
O modelo fica em ~/.cache/w2v_pt (baixado de huggingface.co/onnx-community/wav2vec2-large-xlsr-53-portuguese-ONNX)."""
import json, subprocess, unicodedata
from pathlib import Path
import numpy as np

PASTA = Path.home() / ".cache" / "w2v_pt"
ARQS = {"onnx/model_q4.onnx": "model_q4.onnx", "vocab.json": "vocab.json"}
REPO = "https://huggingface.co/onnx-community/wav2vec2-large-xlsr-53-portuguese-ONNX/resolve/main/"
SR = 16000
_sess, _voc = None, None


def _carregar():
    global _sess, _voc
    if _sess is None:
        PASTA.mkdir(parents=True, exist_ok=True)
        for remoto, local in ARQS.items():
            if not (PASTA / local).exists():
                subprocess.run(["curl", "-sL", "-o", str(PASTA / local), REPO + remoto], check=True)
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = 4
        _sess = ort.InferenceSession(str(PASTA / "model_q4.onnx"), so, providers=["CPUExecutionProvider"])
        _voc = json.load(open(PASTA / "vocab.json"))
    return _sess, _voc


def _letras(palavra, voc):
    """Letras da palavra que o modelo conhece (acentos do PT ficam; o resto vira a letra base ou some)."""
    out = []
    for ch in palavra.lower():
        if ch in voc and ch not in ("|", "<pad>", "<s>", "</s>", "<unk>"):
            out.append(voc[ch]); continue
        base = unicodedata.normalize("NFKD", ch)[0]
        if base in voc and base.isalpha():
            out.append(voc[base])
    return out


def _emissoes(audio):
    sess, _ = _carregar()
    x = (audio - audio.mean()) / (audio.std() + 1e-7)
    logits = sess.run(None, {sess.get_inputs()[0].name: x[None].astype(np.float32)})[0][0]
    m = logits.max(1, keepdims=True)
    return logits - m - np.log(np.exp(logits - m).sum(1, keepdims=True))      # log-softmax (T, V)


def _viterbi(lp, alvo, branco=0):
    """CTC forçado: devolve, para cada letra do alvo, (quadro inicial, quadro final)."""
    T, L = lp.shape[0], len(alvo)
    S = 2 * L + 1
    rot = np.full(S, branco); rot[1::2] = alvo
    NEG = -1e9
    dp = np.full(S, NEG); dp[0] = lp[0, branco]
    if S > 1:
        dp[1] = lp[0, rot[1]]
    volta = np.zeros((T, S), np.int8)                                   # 0 = fica, 1 = veio de s-1, 2 = de s-2
    pode2 = np.zeros(S, bool); pode2[3::2] = rot[3::2] != rot[1:-2:2]
    for t in range(1, T):
        a = dp
        b = np.concatenate([[NEG], dp[:-1]])
        c = np.concatenate([[NEG, NEG], dp[:-2]]); c = np.where(pode2, c, NEG)
        pilha = np.stack([a, b, c]); k = pilha.argmax(0)
        dp = pilha[k, np.arange(S)] + lp[t, rot]
        volta[t] = k
    s = int(S - 1 if S == 1 or dp[S - 1] >= dp[S - 2] else S - 2)
    caminho = np.zeros(T, int)
    for t in range(T - 1, -1, -1):
        caminho[t] = s
        s -= int(volta[t, s])
    spans = [[None, None] for _ in range(L)]
    for t, st in enumerate(caminho):
        if st % 2 == 1:
            j = st // 2
            if spans[j][0] is None:
                spans[j][0] = t
            spans[j][1] = t
    return spans


def forcar(wav, palavras, tempos, grupos, margem=0.5):
    """palavras: tokens do roteiro; tempos: [(ini, fim)] aproximados (Whisper); grupos: [(i0, i1)] = palavras de cada
    frase. Devolve os tempos refinados (as palavras sem letras conhecidas ficam com o tempo antigo)."""
    _, voc = _carregar()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    novos = [tuple(t) for t in tempos]
    sep = voc["|"]
    for i0, i1 in grupos:
        if i1 <= i0:
            continue
        a = max(0.0, tempos[i0][0] - margem)
        b = min(len(audio) / SR, tempos[i1 - 1][1] + margem)
        if i1 < len(tempos):
            b = min(b, tempos[i1][0] + 0.05)           # não invade a frase seguinte
        if i0 > 0:
            a = max(a, tempos[i0 - 1][1] - 0.05)
        trecho = audio[int(a * SR):int(b * SR)]
        if len(trecho) < SR * 0.3:
            continue
        lp = _emissoes(trecho)
        alvo, dono = [], []
        for w in range(i0, i1):
            ls = _letras(palavras[w], voc)
            if alvo and ls:
                alvo.append(sep); dono.append(None)
            for l_ in ls:
                alvo.append(l_); dono.append(w)
        if not alvo or len(alvo) > lp.shape[0]:
            continue
        spans = _viterbi(lp, alvo)
        dq = (b - a) / lp.shape[0]
        por = {}
        for (q0, q1), w in zip(spans, dono):
            if w is None or q0 is None:
                continue
            ini, fim = por.get(w, (q0, q1))
            por[w] = (min(ini, q0), max(fim, q1))
        for w, (q0, q1) in por.items():
            novos[w] = (round(a + q0 * dq, 3), round(a + (q1 + 1) * dq, 3))
    return novos
