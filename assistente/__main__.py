"""Linha de comando.

Exemplos:
    python -m assistente rodar                      # carrossel: pesquisa, cria e publica
    python -m assistente rodar --formato imagem     # post de imagem única (curiosidade)
    python -m assistente rodar --sem-publicar       # só cria (para revisar antes)
    python -m assistente gerar --tema "Kafka e A Metamorfose"
    python -m assistente publicar posts/2026-10-07_0900_kafka
    python -m assistente testar-imagem --mundo aquarela  # testa só a geração de imagens

Rotina agendada no Claude Code (sem chave da API):
    python -m assistente contexto --formato carrossel     # instruções do guia para o post
    python -m assistente nova-pasta --formato carrossel --tema "Drácula"
    python -m assistente validar posts/<pasta>             # confere o post.json escrito
    python -m assistente montar --pendentes                # gera imagens e legenda (GitHub)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from . import geracao_imagens, imagens, pipeline, rotina
from .config import carregar
from .modelos import FORMATOS, Post, Slide


def _resolver_pasta(cfg, caminho: str | None) -> Path:
    if not caminho:
        raise SystemExit("Informe a pasta do post.")
    pasta = Path(caminho)
    if not pasta.is_absolute() and not pasta.exists():
        pasta = cfg.raiz / pasta
    return pasta


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

    p_ctx = sub.add_parser("contexto", help="mostra as instruções do guia para escrever um post")
    p_ctx.add_argument("--formato", choices=FORMATOS, default="carrossel")
    p_ctx.add_argument("--tema", help="força um tema")

    p_nova = sub.add_parser("nova-pasta", help="cria a pasta de um post novo e mostra o caminho")
    p_nova.add_argument("--formato", choices=FORMATOS, default="carrossel")
    p_nova.add_argument("--tema", required=True)

    p_val = sub.add_parser("validar", help="confere um post.json contra as regras do guia")
    p_val.add_argument("pasta")

    p_mon = sub.add_parser("montar", help="gera imagens, slides e legenda a partir de post.json")
    p_mon.add_argument("pasta", nargs="?")
    p_mon.add_argument("--pendentes", action="store_true", help="monta todos os posts ainda sem imagens")

    p_teste = sub.add_parser("testar-imagem", help="gera uma imagem de teste (não usa Claude nem Instagram)")
    p_teste.add_argument("--mundo", default="aquarela", help="mundo visual do config.yaml")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = carregar(args.config)

    if args.comando == "testar-imagem":
        return testar_imagem(cfg, args.mundo)
    if args.comando == "contexto":
        print(rotina.briefing(cfg, args.formato, args.tema))
        return 0
    if args.comando == "nova-pasta":
        print(rotina.nova_pasta(cfg, args.formato, args.tema).relative_to(cfg.raiz))
        return 0
    if args.comando == "validar":
        problemas = rotina.validar(cfg, _resolver_pasta(cfg, args.pasta))
        for problema in problemas:
            print(f"- {problema}")
        print("OK: post pronto." if not problemas else f"{len(problemas)} problema(s) para corrigir.")
        return 1 if problemas else 0
    if args.comando == "montar":
        pastas = rotina.pendentes(cfg) if args.pendentes else [_resolver_pasta(cfg, args.pasta)]
        for pasta in pastas:
            pipeline.montar(cfg, pasta)
            print(f"Montado: {pasta.relative_to(cfg.raiz)}")
        _saida_github("pastas", " ".join(str(p.relative_to(cfg.raiz)) for p in pastas))
        return 0

    if args.comando in ("rodar", "gerar"):
        pasta = pipeline.gerar(cfg, formato=args.formato, tema=args.tema)
        _saida_github("pasta", str(pasta.relative_to(cfg.raiz)))
        print(f"Post gerado em: {pasta}")
        if args.comando == "gerar" or args.sem_publicar:
            return 0
    else:
        pasta = _resolver_pasta(cfg, args.pasta)

    resultado = pipeline.publicar(cfg, pasta)
    _saida_github("permalink", resultado.get("permalink", ""))
    print(f"Publicado: {resultado.get('permalink') or resultado.get('midia_id')}")
    return 0


CENA_TESTE = (
    "An old wooden desk by a window at dusk with a stack of classic books, an open notebook, "
    "a fountain pen and a cup of tea, eye-level still life with a 50mm lens"
)


def testar_imagem(cfg, mundo: str) -> int:
    """Gera uma cena no mundo visual escolhido e um slide de exemplo com o layout da marca."""
    if mundo not in cfg.secao("mundos_visuais"):
        print(f"Mundo visual desconhecido: {mundo}. Opções: {', '.join(cfg.secao('mundos_visuais'))}")
        return 2
    if cfg.secao("imagens_ia").get("provedor") == "pollinations" and not os.environ.get("POLLINATIONS_TOKEN"):
        print("Atenção: POLLINATIONS_TOKEN não está definido; o teste vai usar o modelo anônimo, mais fraco.")
    prompt = geracao_imagens.montar_prompt(cfg, CENA_TESTE, mundo)
    fundo = geracao_imagens.gerar_ilustracao(cfg, prompt, semente=42, tentativas=2)
    if fundo is None:
        print("Não foi possível gerar a imagem. Veja as mensagens acima (chave inválida ou sem créditos?).")
        return 1
    pasta = cfg.raiz / "posts" / "_teste"
    pasta.mkdir(parents=True, exist_ok=True)
    fundo.save(pasta / f"{mundo}_cena.jpg", quality=92)
    vazio = dict(texto="", citacao="", autor_citacao="", diagrama_de="", diagrama_para="",
                 diagrama_legenda="", prompt_imagem=CENA_TESTE)
    exemplo = Post(tema="teste", pilar="", mundo_visual=mundo, isbn_capa="", legenda="", hashtags=[], fontes=[],
                   slides=[Slide(rotulo="Teste de imagem", titulo=f"Mundo visual: *{mundo}*",
                                 **{**vazio, "texto": "Assim fica o texto da marca sobre a cena gerada."})])
    caminho = imagens.gerar(cfg, "imagem", exemplo, pasta, [fundo])[0]
    caminho = caminho.rename(pasta / f"{mundo}_slide.jpg")
    _saida_github("pasta", str(pasta.relative_to(cfg.raiz)))
    print(f"Imagem de teste salva em: {pasta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
