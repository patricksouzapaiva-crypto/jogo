"""Substituto mínimo do torchaudio só para gerar som com o stable-audio-tools (o torchaudio do PyPI não existe para o
torch 2.15 desta máquina). Só a reamostragem é usada na geração; o resto levanta erro claro se alguém precisar."""
from . import transforms, functional  # noqa: F401
__version__ = "0-shim"


def load(*a, **k):
    raise NotImplementedError("torchaudio shim: use ffmpeg para ler áudio")


def save(*a, **k):
    raise NotImplementedError("torchaudio shim: use ffmpeg para gravar áudio")
