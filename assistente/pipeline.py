"""Junta as etapas: pesquisar -> redigir -> gerar imagens -> publicar."""

from __future__ import annotations

import datetime as dt
import json
import logging
import random
import re
import unicodedata
from pathlib import Path

from . import capas, geracao_imagens, hospedagem, historico, ia, imagens
from .config import Config, segredo
from .instagram import Instagram
from .modelos import FORMATOS, Post, montar_legenda

log = logging.getLogger(__name__)


def _slug(texto: str, limite: int = 50) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:limite].rstrip("-") or "post"


def gerar(cfg: Config, formato: str = "carrossel", tema: str | None = None) -> Path:
    """Pesquisa, escreve e desenha um post. Devolve a pasta onde tudo foi salvo."""
    if formato not in FORMATOS:
        raise ValueError(f"Formato desconhecido: {formato} (use {' ou '.join(FORMATOS)}).")
    arquivo_hist = cfg.arquivo_historico
    log.info("Pesquisando tema para %s%s...", formato, f" '{tema}'" if tema else "")
    dossie = ia.pesquisar(
        cfg,
        temas_usados=historico.temas_recentes(arquivo_hist),
        pilares_usados=historico.pilares_recentes(arquivo_hist),
        tema=tema,
        formato=formato,
    )
    mundos = historico.mundos_recentes(arquivo_hist)
    log.info("Escrevendo o post...")
    post = ia.redigir(cfg, dossie, formato, mundos)
    if cfg.ia.get("revisao", True):
        log.info("Revisando o post...")
        post = ia.revisar(cfg, dossie, post, formato, mundos)

    agora = dt.datetime.now()
    post_id = f"{agora:%Y-%m-%d_%H%M%S}_{formato}_{_slug(post.tema)}"
    pasta = cfg.pasta_posts / post_id
    pasta.mkdir(parents=True, exist_ok=True)

    prompts = [geracao_imagens.montar_prompt(cfg, s.prompt_imagem, post.mundo_visual) for s in post.slides]
    semente = random.randint(1, 999_999)  # a mesma semente no post inteiro deixa o visual coeso
    fundos = geracao_imagens.gerar_para_slides(cfg, prompts, semente)

    capa_livro, origem_capa = None, ""
    if formato == "carrossel" and post.isbn_capa and cfg.visual.get("capa_do_livro", True):
        achado = capas.buscar(post.isbn_capa, cfg.raiz / "marca" / "capas")
        if achado:
            capa_livro, origem_capa = achado

    log.info("Desenhando %d slides...", len(post.slides))
    imagens.gerar(cfg, formato, post, pasta, fundos, capa_livro)

    legenda = montar_legenda(
        post,
        hashtags_fixas=cfg.post.get("hashtags_fixas") or [],
        maximo=int(cfg.post.get("hashtags_maximo", 12)),
    )
    (pasta / "dossie.md").write_text(dossie + "\n", encoding="utf-8")
    dados = {"formato": formato, "origem_capa_livro": origem_capa, **post.model_dump()}
    (pasta / "post.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (pasta / "legenda.txt").write_text(legenda + "\n", encoding="utf-8")
    (pasta / "prompts_imagens.md").write_text(
        "".join(f"## Slide {i}\n\n{p}\n\n" for i, p in enumerate(prompts, start=1)), encoding="utf-8"
    )

    historico.registrar(arquivo_hist, {
        "id": post_id,
        "data": agora.isoformat(timespec="seconds"),
        "formato": formato,
        "tema": post.tema,
        "pilar": post.pilar,
        "mundo_visual": post.mundo_visual,
        "status": "gerado",
        "imagens_ia": sum(f is not None for f in fundos),
    })
    log.info("Post gerado em %s", pasta)
    return pasta


def _ler_post(pasta: Path) -> Post:
    dados = json.loads((pasta / "post.json").read_text(encoding="utf-8"))
    dados.pop("formato", None)
    dados.pop("origem_capa_livro", None)
    return Post.model_validate(dados)


def publicar(cfg: Config, pasta: Path) -> dict[str, str]:
    """Publica no Instagram um post já gerado (a legenda pode ter sido editada à mão)."""
    pasta = Path(pasta)
    registro = pasta / "publicacao.json"
    if registro.exists():
        log.info("Este post já foi publicado; nada a fazer.")
        return json.loads(registro.read_text(encoding="utf-8"))

    post = _ler_post(pasta)
    legenda = (pasta / "legenda.txt").read_text(encoding="utf-8").strip()
    caminhos = sorted(pasta.glob("slide_*.jpg"))

    log.info("Enviando %d imagens para a hospedagem...", len(caminhos))
    urls = hospedagem.publicar_imagens(cfg, caminhos)

    pub = cfg.publicacao
    cliente = Instagram(
        usuario_id=segredo("IG_USER_ID"),
        token=segredo("IG_ACCESS_TOKEN"),
        host=pub.get("graph_host", "https://graph.facebook.com"),
        versao=pub.get("graph_versao", "v23.0"),
    )
    log.info("Publicando no Instagram...")
    resultado = cliente.publicar(urls, legenda)
    resultado["publicado_em"] = dt.datetime.now().isoformat(timespec="seconds")
    registro.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    historico.registrar(cfg.arquivo_historico, {
        "id": pasta.name,
        "tema": post.tema,
        "pilar": post.pilar,
        "status": "publicado",
        "permalink": resultado.get("permalink", ""),
        "midia_id": resultado.get("midia_id", ""),
    })
    return resultado
