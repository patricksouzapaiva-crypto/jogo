"""Leitura do config.yaml e das variáveis de ambiente (segredos)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    dados: dict[str, Any]
    raiz: Path = RAIZ

    def secao(self, nome: str) -> dict[str, Any]:
        return self.dados.get(nome) or {}

    @property
    def perfil(self) -> dict[str, Any]:
        return self.secao("perfil")

    @property
    def post(self) -> dict[str, Any]:
        return self.secao("post")

    @property
    def ia(self) -> dict[str, Any]:
        return self.secao("ia")

    @property
    def visual(self) -> dict[str, Any]:
        return self.secao("visual")

    @property
    def publicacao(self) -> dict[str, Any]:
        return self.secao("publicacao")

    @property
    def pilares(self) -> list[str]:
        return list(self.dados.get("pilares") or [])

    @property
    def regras(self) -> list[str]:
        return list(self.dados.get("regras") or [])

    @property
    def pasta_posts(self) -> Path:
        return self.raiz / "posts"

    @property
    def arquivo_historico(self) -> Path:
        return self.raiz / "data" / "historico.json"


def carregar(caminho: str | Path | None = None) -> Config:
    caminho = Path(caminho) if caminho else RAIZ / "config.yaml"
    with open(caminho, encoding="utf-8") as f:
        dados = yaml.safe_load(f) or {}
    return Config(dados=dados, raiz=caminho.resolve().parent)


def segredo(nome: str) -> str:
    valor = os.environ.get(nome, "").strip()
    if not valor:
        raise RuntimeError(
            f"A variável de ambiente {nome} não está definida. "
            "Veja a seção 'Configuração' do README."
        )
    return valor
