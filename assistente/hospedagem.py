"""Coloca as imagens num endereço público, porque a API do Instagram baixa as imagens por URL."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import requests

from .config import Config, segredo


def _imgbb(caminho: Path) -> str:
    chave = segredo("IMGBB_API_KEY")
    with open(caminho, "rb") as f:
        conteudo = base64.b64encode(f.read()).decode()
    r = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": chave, "image": conteudo, "name": caminho.stem},
        timeout=120,
    )
    r.raise_for_status()
    dados = r.json()
    if not dados.get("success"):
        raise RuntimeError(f"ImgBB recusou o upload: {dados}")
    return dados["data"]["url"]


def _github(caminho: Path, raiz: Path) -> str:
    """Link raw do GitHub. Só funciona com repositório público e com a imagem já enviada (push)."""
    repo = segredo("GITHUB_REPOSITORY")
    # IMAGENS_REF: commit que já contém as imagens (o workflow define depois do push)
    ref = os.environ.get("IMAGENS_REF") or os.environ.get("GITHUB_SHA") or "main"
    relativo = caminho.resolve().relative_to(raiz.resolve()).as_posix()
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{relativo}"


def publicar_imagens(cfg: Config, caminhos: list[Path]) -> list[str]:
    modo = str(cfg.publicacao.get("hospedagem", "imgbb")).lower()
    if modo == "imgbb":
        return [_imgbb(c) for c in caminhos]
    if modo == "github":
        return [_github(c, cfg.raiz) for c in caminhos]
    raise ValueError(f"Hospedagem desconhecida: {modo} (use 'imgbb' ou 'github').")
