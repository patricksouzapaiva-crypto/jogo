"""Histórico de posts, usado para não repetir temas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ler(caminho: Path) -> list[dict[str, Any]]:
    if not caminho.exists():
        return []
    texto = caminho.read_text(encoding="utf-8").strip()
    return json.loads(texto) if texto else []


def salvar(caminho: Path, itens: list[dict[str, Any]]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def registrar(caminho: Path, entrada: dict[str, Any]) -> None:
    """Adiciona a entrada ou atualiza a que tiver o mesmo id."""
    itens = ler(caminho)
    for i, item in enumerate(itens):
        if item.get("id") == entrada.get("id"):
            itens[i] = {**item, **entrada}
            break
    else:
        itens.append(entrada)
    salvar(caminho, itens)


def temas_recentes(caminho: Path, limite: int = 60) -> list[str]:
    return [item["tema"] for item in ler(caminho)[-limite:] if item.get("tema")]


def pilares_recentes(caminho: Path, limite: int = 5) -> list[str]:
    return [item["pilar"] for item in ler(caminho)[-limite:] if item.get("pilar")]
