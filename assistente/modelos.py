"""Estrutura do post gerado pela IA."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

LIMITE_LEGENDA_INSTAGRAM = 2200
LIMITE_HASHTAGS_INSTAGRAM = 30


class Slide(BaseModel):
    titulo: str = Field(description="Título curto do slide, até ~40 caracteres.")
    texto: str = Field(description="Texto do slide, até ~260 caracteres, frases curtas.")


class Post(BaseModel):
    tema: str = Field(description="Identificação curta e específica do tema, para o histórico.")
    pilar: str = Field(description="Qual pilar de conteúdo este post atende (copie o texto do pilar).")
    titulo_capa: str = Field(description="Gancho da capa, até ~60 caracteres, que dá vontade de arrastar.")
    subtitulo_capa: str = Field(description="Complemento da capa, até ~90 caracteres.")
    slides: list[Slide] = Field(description="Slides de conteúdo do carrossel, em ordem.")
    chamada_final: str = Field(description="Texto do último slide: convite para salvar, comentar ou seguir.")
    legenda: str = Field(description="Legenda do post, sem hashtags.")
    hashtags: list[str] = Field(description="Hashtags relevantes, cada uma começando com #.")
    fontes: list[str] = Field(description="URLs das fontes usadas para checar os fatos.")
    prompt_imagem: str = Field(
        description=(
            "Descrição em inglês de uma ilustração para o fundo da capa: cena ou objeto concreto "
            "ligado ao tema, sem texto, sem letras e sem rostos de pessoas reais."
        )
    )


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
