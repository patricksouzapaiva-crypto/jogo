"""Junta as etapas: pesquisar -> redigir -> gerar imagens -> publicar."""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
import unicodedata
from pathlib import Path

from . import geracao_imagens, hospedagem, historico, ia, imagens
from .config import Config, segredo
from .instagram import Instagram
from .modelos import Post, montar_legenda

log = logging.getLogger(__name__)


def _slug(texto: str, limite: int = 50) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:limite].rstrip("-") or "post"


def gerar(cfg: Config, tema: str | None = None) -> Path:
    """Pesquisa, escreve e desenha um post. Devolve a pasta onde tudo foi salvo."""
    arquivo_hist = cfg.arquivo_historico
    log.info("Pesquisando tema%s...", f" '{tema}'" if tema else "")
    dossie = ia.pesquisar(
        cfg,
        temas_usados=historico.temas_recentes(arquivo_hist),
        pilares_usados=historico.pilares_recentes(arquivo_hist),
        tema=tema,
    )
    log.info("Escrevendo o post...")
    post = ia.redigir(cfg, dossie)

    agora = dt.datetime.now()
    post_id = f"{agora:%Y-%m-%d_%H%M%S}_{_slug(post.tema)}"
    pasta = cfg.pasta_posts / post_id
    pasta.mkdir(parents=True, exist_ok=True)

    log.info("Gerando ilustração da capa...")
    ilustracao = geracao_imagens.gerar_ilustracao(cfg, post.prompt_imagem)
    log.info("Desenhando %d slides...", len(post.slides) + 2)
    imagens.gerar(cfg, post, pasta, ilustracao)

    legenda = montar_legenda(
        post,
        hashtags_fixas=cfg.post.get("hashtags_fixas") or [],
        maximo=int(cfg.post.get("hashtags_maximo", 12)),
    )
    (pasta / "dossie.md").write_text(dossie + "\n", encoding="utf-8")
    (pasta / "post.json").write_text(post.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (pasta / "legenda.txt").write_text(legenda + "\n", encoding="utf-8")

    historico.registrar(arquivo_hist, {
        "id": post_id,
        "data": agora.isoformat(timespec="seconds"),
        "tema": post.tema,
        "pilar": post.pilar,
        "status": "gerado",
        "ilustracao_ia": ilustracao is not None,
    })
    log.info("Post gerado em %s", pasta)
    return pasta


def publicar(cfg: Config, pasta: Path) -> dict[str, str]:
    """Publica no Instagram um post já gerado (a legenda pode ter sido editada à mão)."""
    pasta = Path(pasta)
    registro = pasta / "publicacao.json"
    if registro.exists():
        log.info("Este post já foi publicado; nada a fazer.")
        return json.loads(registro.read_text(encoding="utf-8"))

    post = Post.model_validate_json((pasta / "post.json").read_text(encoding="utf-8"))
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
