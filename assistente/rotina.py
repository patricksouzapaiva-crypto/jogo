"""Apoio à rotina agendada no Claude Code (sem chave da API).

Fluxo: a rotina roda `contexto` para receber as instruções do guia, pesquisa na web, escreve
`post.json` e `dossie.md` numa pasta criada por `nova-pasta`, confere com `validar` e envia
para o GitHub. O workflow "Publicar posts" então gera as imagens e publica.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from pydantic import ValidationError

from . import historico, ia
from .config import Config
from .modelos import FORMATOS, Post, normalizar_hashtag

PALAVRAS_PROIBIDAS_NO_CTA = ("arraste", "próximo slide", "proximo slide")


def _exemplo_json(formato: str) -> str:
    slide = {
        "rotulo": "", "titulo": "", "texto": "", "citacao": "", "autor_citacao": "",
        "diagrama_de": "", "diagrama_para": "", "diagrama_legenda": "", "prompt_imagem": "",
    }
    exemplo = {
        "formato": formato, "tema": "", "pilar": "", "mundo_visual": "", "isbn_capa": "",
        "slides": [slide], "legenda": "", "hashtags": [], "fontes": [],
    }
    return json.dumps(exemplo, ensure_ascii=False, indent=2)


def briefing(cfg: Config, formato: str, tema: str | None = None) -> str:
    """Todas as instruções que a rotina precisa, geradas das mesmas regras usadas pela API."""
    arquivo = cfg.arquivo_historico
    pesquisa = ia.instrucoes_pesquisa(
        cfg, historico.temas_recentes(arquivo), historico.pilares_recentes(arquivo), tema, formato
    )
    post = ia.instrucoes_post(cfg, formato, historico.mundos_recentes(arquivo))
    return f"""# Briefing do post ({formato}) — {dt.date.today().isoformat()}

## Etapa 1 — Pesquisa
Use as ferramentas de busca e leitura na web para cumprir o pedido abaixo. Salve o dossiê no
arquivo dossie.md da pasta do post.

{pesquisa}

## Etapa 2 — Redação (só com o que está no dossiê)
{post}

## Etapa 3 — Revisão
Releia o post como editor-chefe antes de salvar; não haverá revisão humana.
{ia.CHECKLIST_REVISAO}

## Formato do arquivo post.json
Um único objeto JSON, em UTF-8, com exatamente estes campos (o exemplo mostra 1 slide; o
{formato} precisa de {"1 slide" if formato == "imagem" else "7 slides"}):

{_exemplo_json(formato)}
"""


def nova_pasta(cfg: Config, formato: str, tema: str) -> Path:
    if formato not in FORMATOS:
        raise ValueError(f"Formato desconhecido: {formato}")
    from .pipeline import _slug  # evita import circular

    agora = dt.datetime.now()
    pasta = cfg.pasta_posts / f"{agora:%Y-%m-%d_%H%M%S}_{formato}_{_slug(tema)}"
    pasta.mkdir(parents=True, exist_ok=False)
    return pasta


def ler(pasta: Path) -> tuple[str, Post]:
    dados = json.loads((pasta / "post.json").read_text(encoding="utf-8"))
    formato = dados.pop("formato", "carrossel")
    dados.pop("origem_capa_livro", None)
    return formato, Post.model_validate(dados)


def validar(cfg: Config, pasta: Path) -> list[str]:
    """Confere o post escrito pela rotina contra as regras do guia. Lista vazia = tudo certo."""
    pasta = Path(pasta)
    if not (pasta / "post.json").exists():
        return [f"Não existe {pasta / 'post.json'}"]
    try:
        formato, post = ler(pasta)
    except (json.JSONDecodeError, ValidationError) as erro:
        return [f"post.json inválido: {erro}"]

    problemas = []
    if formato not in FORMATOS:
        problemas.append(f"formato deve ser {' ou '.join(FORMATOS)}, não '{formato}'")
    esperado = 1 if formato == "imagem" else int(cfg.formatos.get("carrossel", {}).get("total_slides", 7))
    if len(post.slides) != esperado:
        problemas.append(f"o {formato} precisa de {esperado} slide(s); vieram {len(post.slides)}")
    if post.mundo_visual not in cfg.secao("mundos_visuais"):
        problemas.append(f"mundo_visual '{post.mundo_visual}' não está no cardápio do config.yaml")
    if not (pasta / "dossie.md").exists() or not (pasta / "dossie.md").read_text(encoding="utf-8").strip():
        problemas.append("falta o dossie.md com a pesquisa e as fontes")
    if not post.fontes:
        problemas.append("fontes está vazio: liste as URLs usadas")
    if not post.legenda.strip():
        problemas.append("legenda está vazia")
    if "#" in post.legenda:
        problemas.append("a legenda não deve ter hashtags (elas vão no campo hashtags)")
    maximo = int(cfg.post.get("hashtags_maximo", 6))
    if len(post.hashtags) > maximo:
        problemas.append(f"hashtags demais: {len(post.hashtags)} (máximo {maximo})")
    if any(not normalizar_hashtag(h) for h in post.hashtags):
        problemas.append("há hashtag vazia ou inválida")
    if post.isbn_capa and len(re.sub(r"[^0-9Xx]", "", post.isbn_capa)) not in (10, 13):
        problemas.append(f"isbn_capa '{post.isbn_capa}' não tem 10 nem 13 dígitos")

    for i, slide in enumerate(post.slides, start=1):
        if not slide.titulo.strip():
            problemas.append(f"slide {i}: titulo vazio")
        if slide.titulo.count("*") % 2:
            problemas.append(f"slide {i}: asteriscos de destaque sem par no titulo")
        if len(slide.prompt_imagem.split()) < 25:
            problemas.append(f"slide {i}: prompt_imagem curto demais (use o padrão completo, 60–120 palavras)")
        if bool(slide.diagrama_de) != bool(slide.diagrama_para):
            problemas.append(f"slide {i}: diagrama precisa de diagrama_de e diagrama_para")
    if formato == "carrossel" and post.slides:
        final = f"{post.slides[-1].titulo} {post.slides[-1].texto}".lower()
        for palavra in PALAVRAS_PROIBIDAS_NO_CTA:
            if palavra in final:
                problemas.append(f'o último slide não pode dizer "{palavra}"')
    return problemas


def pendentes(cfg: Config) -> list[Path]:
    """Pastas com post.json escrito pela rotina e ainda sem imagens/legenda montadas."""
    if not cfg.pasta_posts.exists():
        return []
    return sorted(
        p for p in cfg.pasta_posts.iterdir()
        if p.is_dir() and (p / "post.json").exists() and not (p / "legenda.txt").exists()
    )
