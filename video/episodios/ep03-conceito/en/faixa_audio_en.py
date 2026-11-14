"""Faixa de áudio em inglês para o vídeo em PORTUGUÊS (YouTube Studio → Idiomas → Áudio).
Encaixa cada fala em inglês (tirada do render inglês) no tempo da mesma fala no vídeo português; se não couber,
acelera até 1,25x. Por baixo vão a trilha e os efeitos do vídeo português (stems), e o resultado tem a mesma
duração do vídeo. Uso: faixa_audio_en.py <pt.tempos.json> <dir_tmp_pt> <en.tempos.json> <dir_tmp_en> <duracao_pt> <saida.m4a>"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / "painel"))
from gerar import tokens  # noqa: E402

pt_tempos, pt_tmp, en_tempos, en_tmp, dur, saida = sys.argv[1:7]
dur = float(dur)
SR = 48000


def ler(f, canais=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", str(canais), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    return a.reshape(-1, canais) if canais > 1 else a


def faixas(roteiro):
    r = json.load(open(AQUI.parent / roteiro))
    out, i = [], 0
    for b in r["batidas"]:
        n = len(tokens(b["fala"])); out.append((i, i + n)); i += n
    return out


ptw = json.load(open(pt_tempos))["palavras"]; enw = json.load(open(en_tempos))["palavras"]
ptf, enf = faixas("roteiro.json"), faixas("roteiro_en.json")
assert len(ptf) == len(enf)
voz_en = ler(f"{en_tmp}/audio.wav.voz.wav")
N = int(dur * SR)
pista = np.zeros(N, np.float32)
fim_ant, acelerados = 0.0, 0
for k, ((pa, pb), (ea, eb)) in enumerate(zip(ptf, enf)):
    e0 = enw[ea][1] - 0.08
    e1 = enw[eb - 1][2] + 0.25
    if k + 1 < len(enf):
        e1 = min(e1, enw[enf[k + 1][0]][1] - 0.03)
    seg = voz_en[int(e0 * SR):int(e1 * SR)]
    ini = max(ptw[pa][1] - 0.05, fim_ant + 0.08)
    lim = (ptw[ptf[k + 1][0]][1] - 0.1) if k + 1 < len(ptf) else dur - 4.0
    disp = lim - ini
    if len(seg) / SR > disp > 0.3:
        fator = min(len(seg) / SR / disp, 1.25)
        seg = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                                            "-af", f"atempo={fator:.4f}", "-f", "f32le", "-"],
                                           input=seg.tobytes(), capture_output=True, check=True).stdout, np.float32)
        acelerados += 1
    i0 = int(ini * SR)
    seg = seg[: max(0, N - i0)]
    r = min(len(seg), int(0.01 * SR))
    if r:
        seg = seg.copy(); seg[:r] *= np.linspace(0, 1, r); seg[-r:] *= np.linspace(1, 0, r)
    pista[i0:i0 + len(seg)] += seg
    fim_ant = ini + len(seg) / SR
print(f"falas encaixadas: {len(ptf)}; aceleradas: {acelerados}; última termina em {fim_ant:.1f} s de {dur:.1f} s")
fundo = ler(f"{pt_tmp}/audio.wav.fundo.wav", 2); efe = ler(f"{pt_tmp}/audio.wav.efeitos.wav", 2)
n = min(len(fundo), len(efe), N)
mix = np.zeros((N, 2), np.float32)
mix[:n] += fundo[:n] + efe[:n]
mix += pista[:, None]
cru = Path(saida).with_suffix(".cru.wav")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", str(cru)],
               input=mix.astype(np.float32).tobytes(), check=True)
# dois passos de loudnorm (-14 LUFS), limitador e AAC
m = subprocess.run(["ffmpeg", "-i", str(cru), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
j = json.loads(m[m.rfind("{"):m.rfind("}") + 1])
af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
      f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000,"
      "alimiter=limit=0.79:attack=1:release=50:level=disabled")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(cru), "-af", af, "-ac", "2", "-t", f"{dur:.3f}",
                "-c:a", "aac", "-b:a", "192k", "-aac_is", "0", "-aac_ms", "0", "-aac_pns", "0", saida], check=True)
cru.unlink()
print("pronto:", saida)
