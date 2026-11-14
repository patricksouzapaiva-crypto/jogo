"""Efeitos sonoros sob medida com o Stable Audio Open Small (Stability AI; licença comunitária: uso comercial liberado
abaixo de US$ 1 mi/ano). Roda no processador (~17 s por efeito de até ~11 s). Token do Hugging Face injetado pelo proxy.
Uso: python3 gerar_efeito.py <nome> <segundos> "<descrição em inglês>" [variações]
     → painel/sons/<nome>[_v].mp3 (normalizado em -20 LUFS, como os do Sonniss)
Dica de descrição: o que soa + material + distância/lugar ("close foley", "distant, large room") + "no music"."""
import os, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI / "sao" / "shim"))          # torchaudio mínimo (o do PyPI não existe para este torch)
os.environ.setdefault("HF_TOKEN", "proxy-injected"); os.environ.setdefault("HF_HOME", "/home/user/.cache/hf")
import numpy as np  # noqa: E402
import torch  # noqa: E402
from stable_audio_tools import get_pretrained_model  # noqa: E402
from stable_audio_tools.inference.generation import generate_diffusion_cond  # noqa: E402

SONS = AQUI.parent / "sons"
_m = None


def gerar(nome, seg, texto, var=1, semente=None):
    global _m
    if _m is None:
        _m = get_pretrained_model("stabilityai/stable-audio-open-small")
    model, cfg = _m; sr = cfg["sample_rate"]
    saidas = []
    for v in range(var):
        if semente is not None:
            torch.manual_seed(semente + v)
        out = generate_diffusion_cond(model, steps=8, cfg_scale=1.0, sample_size=cfg["sample_size"], sampler_type="pingpong",
                                      conditioning=[{"prompt": texto, "seconds_total": seg}], device="cpu")
        a = out[0].float().clamp(-1, 1).numpy().T[: int(seg * sr)].astype(np.float32)
        dest = SONS / (f"{nome}.mp3" if var == 1 else f"{nome}_{v + 1}.mp3")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", str(a.shape[1]), "-i", "-",
                        "-af", "afade=t=out:st=%.2f:d=0.4,loudnorm=I=-20:TP=-2:LRA=15" % max(0, seg - 0.4),
                        "-ar", "48000", "-b:a", "192k", str(dest)], input=a.tobytes(), check=True)
        print("ok", dest.name, flush=True); saidas.append(dest)
    return saidas


if __name__ == "__main__":
    a = sys.argv[1:]
    gerar(a[0], float(a[1]), a[2], int(a[3]) if len(a) > 3 else 1)
