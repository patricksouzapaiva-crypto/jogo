import torch
from .functional import resample


class Resample(torch.nn.Module):
    def __init__(self, orig_freq=16000, new_freq=16000, **k):
        super().__init__(); self.o, self.n = orig_freq, new_freq

    def forward(self, x):
        return resample(x, self.o, self.n)


class _NaoTem(torch.nn.Module):
    def __init__(self, *a, **k):
        raise NotImplementedError("torchaudio shim")


MelSpectrogram = Spectrogram = MFCC = _NaoTem
