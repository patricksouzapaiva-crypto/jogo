"""Busca a capa real de uma edição pelo ISBN.

Ordem: arquivo próprio em marca/capas/<ISBN>.jpg (ex.: foto da edição brasileira), depois
Open Library e Google Books. Regra da marca: nunca inventar uma capa. Se não houver uma
imagem real com boa resolução, o slide 1 sai sem capa.
"""

from __future__ import annotations

import io
import logging
import os
import re
from pathlib import Path

import requests
from PIL import Image

log = logging.getLogger(__name__)

ALTURA_MINIMA = 300  # abaixo disso a capa ficaria borrada no slide


def limpar_isbn(isbn: str) -> str:
    return re.sub(r"[^0-9Xx]", "", isbn or "").upper()


def _baixar(url: str) -> Image.Image | None:
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
        return None
    img = Image.open(io.BytesIO(r.content))
    img.load()
    return img.convert("RGB") if img.height >= ALTURA_MINIMA else None


def _open_library(isbn: str) -> tuple[Image.Image, str] | None:
    url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
    img = _baixar(url)
    return (img, url) if img else None


def _google_books(isbn: str) -> tuple[Image.Image, str] | None:
    params = {"q": f"isbn:{isbn}"}
    chave_api = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
    if chave_api:  # opcional: sem chave, a cota anônima do Google costuma acabar
        params["key"] = chave_api
    r = requests.get("https://www.googleapis.com/books/v1/volumes", params=params, timeout=30)
    if r.status_code != 200:
        return None
    for item in r.json().get("items", []):
        links = item.get("volumeInfo", {}).get("imageLinks", {})
        for chave in ("extraLarge", "large", "medium", "thumbnail"):
            if links.get(chave):
                url = links[chave].replace("http://", "https://").replace("&edge=curl", "")
                if chave == "thumbnail":
                    url = url.replace("zoom=1", "zoom=0")
                img = _baixar(url)
                if img:
                    return img, url
    return None


def _arquivo_local(pasta: Path | None, isbn: str) -> tuple[Image.Image, str] | None:
    if not pasta:
        return None
    for extensao in ("jpg", "jpeg", "png", "webp"):
        caminho = pasta / f"{isbn}.{extensao}"
        if caminho.exists():
            return Image.open(caminho).convert("RGB"), f"arquivo local {caminho.name}"
    return None


def buscar(isbn: str, pasta_local: Path | None = None) -> tuple[Image.Image, str] | None:
    """Devolve (imagem da capa, origem) ou None se não achar uma capa real."""
    isbn = limpar_isbn(isbn)
    if len(isbn) not in (10, 13):
        return None
    local = _arquivo_local(pasta_local, isbn)
    if local:
        return local
    for fonte in (_open_library, _google_books):
        try:
            achado = fonte(isbn)
        except (requests.RequestException, OSError) as erro:
            log.warning("Falha ao buscar capa (%s): %s", fonte.__name__, erro)
            continue
        if achado:
            log.info("Capa encontrada: %s", achado[1])
            return achado
    log.info("Nenhuma capa real encontrada para o ISBN %s; o slide 1 sai sem capa.", isbn)
    return None
