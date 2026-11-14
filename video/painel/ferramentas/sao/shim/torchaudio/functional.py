import torch.nn.functional as F


def resample(x, orig_freq, new_freq, **k):
    if orig_freq == new_freq:
        return x
    n = int(round(x.shape[-1] * new_freq / orig_freq))
    return F.interpolate(x.reshape(-1, 1, x.shape[-1]), size=n, mode="linear", align_corners=False).reshape(*x.shape[:-1], n)
