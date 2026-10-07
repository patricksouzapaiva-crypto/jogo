"""Geração das imagens de fundo por IA (Pollinations, Cloudflare, OpenAI ou Gemini).

A IA gera só a cena, sem texto; títulos e textos são escritos por cima pelo
módulo de imagens, porque essas IAs costumam errar letras.
"""

from __future__ import annotations

import base64
import io
import logging
import os
import time
import urllib.parse

import requests
from PIL import Image

from .config import Config, segredo

log = logging.getLogger(__name__)

TIMEOUT = 180


class ChaveInvalida(RuntimeError):
    pass


def validar_chave_pollinations(token: str) -> None:
    """Pega erros comuns de cópia antes de chamar a API, com uma mensagem clara."""
    if "…" in token or "..." in token or not token.isascii():
        raise ChaveInvalida(
            "A POLLINATIONS_TOKEN salva parece abreviada (tem '…'): o site mostra a chave cortada. "
            "Copie a chave inteira (botão de copiar ao criar a chave) e salve de novo o segredo."
        )
    if not token.startswith("sk_"):
        raise ChaveInvalida(
            "A POLLINATIONS_TOKEN deve ser a chave secreta, que começa com 'sk_' (não a 'pk_')."
        )


def _pollinations(prompt: str, opcoes: dict, largura: int, altura: int, semente: int) -> bytes:
    """Com POLLINATIONS_TOKEN usa a API nova (gen.pollinations.ai) e o modelo escolhido;
    sem chave, cai no acesso anônimo antigo, que só tem um modelo mais fraco."""
    token = os.environ.get("POLLINATIONS_TOKEN", "").strip()
    params = {
        "width": largura,
        # um pouco mais alta: o recorte central depois tira a marca d'água do rodapé (acesso anônimo)
        "height": altura + 160,
        "seed": semente,  # mesma semente no post inteiro deixa as imagens mais coesas
        "nologo": "true",
        "private": "true",
    }
    headers = {}
    if token:
        validar_chave_pollinations(token)
        base = opcoes.get("pollinations_url", "https://gen.pollinations.ai/image/")
        params["model"] = opcoes.get("pollinations_modelo", "zimage")
        headers["Authorization"] = f"Bearer {token}"
    else:
        log.warning("POLLINATIONS_TOKEN não definido: usando o acesso anônimo, com um modelo mais fraco. "
                    "Crie a chave gratuita em https://enter.pollinations.ai/keys.")
        base = "https://image.pollinations.ai/prompt/"
    r = requests.get(base + urllib.parse.quote(prompt, safe=""), params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    if not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError(f"Pollinations não devolveu uma imagem: {r.text[:200]}")
    return r.content


def _cloudflare(prompt: str, opcoes: dict, largura: int, altura: int, semente: int) -> bytes:
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


def _openai(prompt: str, opcoes: dict, largura: int, altura: int, semente: int) -> bytes:
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


def _gemini(prompt: str, opcoes: dict, largura: int, altura: int, semente: int) -> bytes:
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


# Layout fixo da marca: texto na metade superior, cena na metade inferior.
COMPOSICAO = (
    "Full-bleed artwork filling the entire frame edge to edge, no border, no frame, no paper "
    "margins, not a picture of a print. Vertical 4:5 composition. The upper half is calm, "
    "uncluttered negative space with low detail to hold overlaid text; the main subject and "
    "action sit in the lower half"
)


def descricao_do_mundo(cfg: Config, mundo: str) -> str:
    mundos = cfg.secao("mundos_visuais")
    dados = mundos.get(mundo) or {}
    return str(dados.get("descricao", "")).strip()


def montar_prompt(cfg: Config, descricao: str, mundo: str) -> str:
    # A técnica vem primeiro: os modelos de imagem dão mais peso ao começo do prompt.
    partes = [descricao_do_mundo(cfg, mundo).rstrip("."), descricao.strip().rstrip("."), COMPOSICAO]
    return ". ".join(p for p in partes if p) + (
        ". No text, no letters, no words, no captions, no signage, no watermark, no logos."
    )


def gerar_ilustracao(cfg: Config, prompt: str, semente: int = 0, tentativas: int = 4) -> Image.Image | None:
    """Gera uma imagem de fundo. Devolve None se estiver desligado ou se falhar."""
    opcoes = cfg.secao("imagens_ia")
    provedor = str(opcoes.get("provedor", "nenhum")).lower()
    if provedor in ("", "nenhum", "none") or not prompt.strip():
        return None
    if provedor not in PROVEDORES:
        log.warning("Provedor de imagens desconhecido: %s. Usando fundo liso.", provedor)
        return None

    largura = int(cfg.visual.get("largura", 1080))
    altura = int(cfg.visual.get("altura", 1350))
    for tentativa in range(1, tentativas + 1):
        try:
            dados = PROVEDORES[provedor](prompt, opcoes, largura, altura, semente)
            img = Image.open(io.BytesIO(dados))
            img.load()
            return recortar(img, largura, altura)
        except ChaveInvalida as erro:
            log.error("%s", erro)
            return None
        except Exception as erro:  # o fundo liso é um bom plano B; o post não deve parar
            motivo = str(erro).split(" for url")[0][:200]  # a URL do prompt é enorme; não poluir o log
            log.warning("Falha ao gerar imagem com %s (tentativa %d/%d): %s",
                        provedor, tentativa, tentativas, motivo)
            if tentativa < tentativas:
                time.sleep(10 * 2 ** (tentativa - 1))
    return None


def gerar_para_slides(cfg: Config, prompts: list[str], semente: int) -> list[Image.Image | None]:
    """Gera uma imagem por slide, com pausa entre elas para respeitar o limite do serviço."""
    opcoes = cfg.secao("imagens_ia")
    if str(opcoes.get("provedor", "nenhum")).lower() in ("", "nenhum", "none"):
        return [None] * len(prompts)
    pausa = float(opcoes.get("pausa_segundos", 3))
    imagens = []
    for i, prompt in enumerate(prompts):
        if i and pausa:
            time.sleep(pausa)
        log.info("Gerando imagem %d/%d...", i + 1, len(prompts))
        imagens.append(gerar_ilustracao(cfg, prompt, semente))
    return imagens
