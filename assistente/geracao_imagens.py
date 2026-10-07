"""Geração da ilustração da capa por IA (Pollinations, Cloudflare, OpenAI ou Gemini).

A IA gera só a ilustração, sem texto; o título é escrito por cima pelo módulo
de imagens, porque essas IAs costumam errar letras.
"""

from __future__ import annotations

import base64
import io
import logging
import os
import urllib.parse

import requests
from PIL import Image

from .config import Config, segredo

log = logging.getLogger(__name__)

TIMEOUT = 180


def _pollinations(prompt: str, opcoes: dict, largura: int, altura: int) -> bytes:
    base = opcoes.get("pollinations_url", "https://image.pollinations.ai/prompt/")
    params = {
        "width": largura,
        # um pouco mais alta: o recorte central depois tira a marca d'água do rodapé
        "height": altura + 160,
        "model": opcoes.get("pollinations_modelo", "flux"),
        "nologo": "true",
        "private": "true",
    }
    headers = {}
    token = os.environ.get("POLLINATIONS_TOKEN", "").strip()
    if token:  # opcional: token gratuito aumenta o limite de uso
        headers["Authorization"] = f"Bearer {token}"
    url = base + urllib.parse.quote(prompt, safe="")
    r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content


def _cloudflare(prompt: str, opcoes: dict, largura: int, altura: int) -> bytes:
    conta = segredo("CLOUDFLARE_ACCOUNT_ID")
    token = segredo("CLOUDFLARE_API_TOKEN")
    modelo = opcoes.get("cloudflare_modelo", "@cf/black-forest-labs/flux-1-schnell")
    r = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{conta}/ai/run/{modelo}",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": prompt, "steps": 8},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return base64.b64decode(r.json()["result"]["image"])


def _openai(prompt: str, opcoes: dict, largura: int, altura: int) -> bytes:
    chave = segredo("OPENAI_API_KEY")
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {chave}"},
        json={
            "model": opcoes.get("openai_modelo", "gpt-image-1"),
            "prompt": prompt,
            "size": "1024x1536",  # retrato; depois é recortado para 4:5
            "quality": opcoes.get("openai_qualidade", "medium"),
            "n": 1,
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return base64.b64decode(r.json()["data"][0]["b64_json"])


def _gemini(prompt: str, opcoes: dict, largura: int, altura: int) -> bytes:
    chave = segredo("GEMINI_API_KEY")
    modelo = opcoes.get("gemini_modelo", "gemini-2.5-flash-image")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
        headers={"x-goog-api-key": chave},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    for candidato in r.json().get("candidates", []):
        for parte in candidato.get("content", {}).get("parts", []):
            dados = parte.get("inlineData") or parte.get("inline_data")
            if dados and dados.get("data"):
                return base64.b64decode(dados["data"])
    raise RuntimeError("O Gemini não devolveu nenhuma imagem.")


PROVEDORES = {
    "pollinations": _pollinations,
    "cloudflare": _cloudflare,
    "openai": _openai,
    "gemini": _gemini,
}


def recortar(img: Image.Image, largura: int, altura: int) -> Image.Image:
    """Redimensiona e recorta pelo centro até o tamanho exato do slide."""
    img = img.convert("RGB")
    escala = max(largura / img.width, altura / img.height)
    img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    x = (img.width - largura) // 2
    y = (img.height - altura) // 2
    return img.crop((x, y, x + largura, y + altura))


def gerar_ilustracao(cfg: Config, descricao: str) -> Image.Image | None:
    """Gera a ilustração da capa. Devolve None se estiver desligado ou se falhar."""
    opcoes = cfg.secao("imagens_ia")
    provedor = str(opcoes.get("provedor", "nenhum")).lower()
    if provedor in ("", "nenhum", "none") or not descricao.strip():
        return None
    if provedor not in PROVEDORES:
        log.warning("Provedor de imagens desconhecido: %s. Usando capa sem ilustração.", provedor)
        return None

    largura = int(cfg.visual.get("largura", 1080))
    altura = int(cfg.visual.get("altura", 1350))
    estilo = str(opcoes.get("estilo", "")).strip()
    prompt = (
        f"{descricao.strip()}. {estilo} "
        "No text, no letters, no words, no watermark, no logos."
    ).strip()

    try:
        dados = PROVEDORES[provedor](prompt, opcoes, largura, altura)
        img = Image.open(io.BytesIO(dados))
        img.load()
        return recortar(img, largura, altura)
    except Exception as erro:  # a capa tipográfica é um bom plano B; o post não deve parar
        log.warning("Falha ao gerar ilustração com %s (%s). Usando capa sem ilustração.", provedor, erro)
        return None
