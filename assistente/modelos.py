"""Estrutura do post gerado pela IA."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

LIMITE_LEGENDA_INSTAGRAM = 2200
LIMITE_HASHTAGS_INSTAGRAM = 30

FORMATOS = ("carrossel", "imagem")


class Slide(BaseModel):
    rotulo: str = Field(
        description="Rótulo curto acima do título, em MAIÚSCULAS (ex.: CURIOSIDADE LITERÁRIA, "
        "SHAKESPEARE • ROMEU E JULIETA). Vazio se não houver."
    )
    titulo: str = Field(
        description="Título do slide. Marque entre *asteriscos* de 1 a 3 palavras para destacar em "
        "vermelho (ex.: 'Dez anos depois, ele *voltou.*')."
    )
    texto: str = Field(description="Texto de apoio, de 1 a 3 frases curtas. Vazio se não houver.")
    citacao: str = Field(description="Citação literal e verificada (só na capa). Vazio se não houver.")
    autor_citacao: str = Field(description="Autor da citação. Vazio se não houver citação.")
    diagrama_de: str = Field(
        description="Esquema 'A → B' opcional: palavra de origem (ex.: ERRO). Vazio se não houver."
    )
    diagrama_para: str = Field(description="Esquema 'A → B': palavra de destino (ex.: SOFRIMENTO).")
    diagrama_legenda: str = Field(description="Legenda curta do esquema (ex.: A lógica dos amigos).")
    prompt_imagem: str = Field(
        description="Descrição em inglês da cena de fundo deste slide, sem texto e sem letras."
    )


class Post(BaseModel):
    tema: str = Field(description="Identificação curta e específica do tema, para o histórico.")
    pilar: str = Field(description="Qual pilar de conteúdo este post atende (copie o texto do pilar).")
    mundo_visual: str = Field(description="Nome de um dos mundos visuais disponíveis, para o post inteiro.")
    isbn_capa: str = Field(
        description="ISBN de uma edição identificável (de preferência brasileira) que está no dossiê, "
        "para mostrar a capa real no slide 1. Vazio se não houver ou se o tema não for um livro."
    )
    slides: list[Slide] = Field(description="Slides do post, em ordem.")
    legenda: str = Field(description="Legenda do post, sem hashtags.")
    hashtags: list[str] = Field(description="Hashtags relevantes, cada uma começando com #.")
    fontes: list[str] = Field(description="URLs das fontes usadas para checar os fatos.")


def sem_marcacao(texto: str) -> str:
    return texto.replace("*", "")


def trechos_destacados(texto: str) -> list[list[tuple[str, bool]]]:
    """Divide 'Dez anos depois, ele *voltou.*' em palavras com a marcação de destaque.

    Cada palavra é uma lista de pedaços (texto, destacado), para que pontuação colada a um
    trecho destacado ('*julgamentos*,') continue grudada na palavra.
    """
    palavras: list[list[tuple[str, bool]]] = []
    colar = False  # o pedaço anterior terminou sem espaço: o próximo continua a mesma palavra
    for i, parte in enumerate(texto.split("*")):
        if not parte:
            continue
        destaque = i % 2 == 1
        pedacos = parte.split()
        if not pedacos:
            colar = False
            continue
        if colar and palavras and not parte[0].isspace():
            palavras[-1].append((pedacos.pop(0), destaque))
        palavras.extend([(p, destaque)] for p in pedacos)
        colar = not parte[-1].isspace()
    return palavras


def normalizar_hashtag(tag: str) -> str:
    tag = re.sub(r"[^\w]", "", tag.strip().lstrip("#"))
    return f"#{tag}" if tag else ""


def montar_legenda(post: Post, hashtags_fixas: list[str] | None = None, maximo: int = 12) -> str:
    """Junta legenda + hashtags respeitando os limites do Instagram."""
    maximo = min(maximo, LIMITE_HASHTAGS_INSTAGRAM)
    tags: list[str] = []
    for bruta in [*(hashtags_fixas or []), *post.hashtags]:
        tag = normalizar_hashtag(bruta)
        if tag and tag.lower() not in {t.lower() for t in tags}:
            tags.append(tag)
    tags = tags[:maximo]

    bloco_tags = " ".join(tags)
    corpo = post.legenda.strip()
    espaco = LIMITE_LEGENDA_INSTAGRAM - (len(bloco_tags) + 2 if bloco_tags else 0)
    if len(corpo) > espaco:
        corpo = corpo[: max(espaco - 1, 0)].rstrip() + "…"
    return f"{corpo}\n\n{bloco_tags}" if bloco_tags else corpo
