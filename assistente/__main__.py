"""Linha de comando.

Exemplos:
    python -m assistente rodar                      # carrossel: pesquisa, cria e publica
    python -m assistente rodar --formato imagem     # post de imagem única (curiosidade)
    python -m assistente rodar --sem-publicar       # só cria (para revisar antes)
    python -m assistente gerar --tema "Kafka e A Metamorfose"
    python -m assistente publicar posts/2026-10-07_0900_kafka
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import pipeline
from .config import carregar
from .modelos import FORMATOS


def _saida_github(nome: str, valor: str) -> None:
    arquivo = os.environ.get("GITHUB_OUTPUT")
    if arquivo:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(f"{nome}={valor}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="assistente", description="Assistente automático de Instagram")
    parser.add_argument("--config", help="caminho do config.yaml (padrão: raiz do projeto)")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_rodar = sub.add_parser("rodar", help="pesquisa, cria e publica um post")
    p_rodar.add_argument("--tema", help="força um tema em vez de deixar a IA escolher")
    p_rodar.add_argument("--formato", choices=FORMATOS, default="carrossel")
    p_rodar.add_argument("--sem-publicar", action="store_true", help="só gera o post, sem publicar")

    p_gerar = sub.add_parser("gerar", help="pesquisa e cria um post, sem publicar")
    p_gerar.add_argument("--tema", help="força um tema em vez de deixar a IA escolher")
    p_gerar.add_argument("--formato", choices=FORMATOS, default="carrossel")

    p_pub = sub.add_parser("publicar", help="publica um post já gerado")
    p_pub.add_argument("pasta", help="pasta do post (ex.: posts/2026-10-07_0900_tema)")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = carregar(args.config)

    if args.comando in ("rodar", "gerar"):
        pasta = pipeline.gerar(cfg, formato=args.formato, tema=args.tema)
        _saida_github("pasta", str(pasta.relative_to(cfg.raiz)))
        print(f"Post gerado em: {pasta}")
        if args.comando == "gerar" or args.sem_publicar:
            return 0
    else:
        pasta = Path(args.pasta)
        if not pasta.is_absolute():
            pasta = (cfg.raiz / pasta) if not pasta.exists() else pasta

    resultado = pipeline.publicar(cfg, pasta)
    _saida_github("permalink", resultado.get("permalink", ""))
    print(f"Publicado: {resultado.get('permalink') or resultado.get('midia_id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
