"""Pesquisa (com busca na web) e redação do post usando o Claude."""

from __future__ import annotations

import datetime as dt
import logging

import anthropic

from .config import Config
from .modelos import Post

log = logging.getLogger(__name__)

# Se um pedido for recusado pelos filtros de segurança, a API refaz o pedido
# automaticamente em outro modelo recomendado (fallback no servidor).
BETAS = ["server-side-fallback-2026-07-01"]
MAX_CONTINUACOES = 5


class ErroIA(RuntimeError):
    pass


def _cliente() -> anthropic.Anthropic:
    return anthropic.Anthropic(max_retries=4)


def _texto(resposta) -> str:
    return "\n".join(b.text for b in resposta.content if b.type == "text").strip()


def _checar_parada(resposta) -> None:
    if resposta.stop_reason == "refusal":
        detalhe = getattr(resposta, "stop_details", None)
        raise ErroIA(f"A IA recusou o pedido: {detalhe}")
    if resposta.stop_reason == "max_tokens":
        raise ErroIA("A resposta da IA foi cortada (max_tokens).")


def _perfil(cfg: Config) -> str:
    p = cfg.perfil
    return (
        f"Perfil: {p.get('nome', '')} ({p.get('arroba', '')})\n"
        f"Idioma: {p.get('idioma', 'português do Brasil')}\n"
        f"Público: {str(p.get('publico', '')).strip()}\n"
        f"Tom de voz: {str(p.get('tom_de_voz', '')).strip()}"
    )


def pesquisar(cfg: Config, temas_usados: list[str], pilares_usados: list[str], tema: str | None = None) -> str:
    """Escolhe um tema (se não for informado) e monta um dossiê com fatos verificados na web."""
    hoje = dt.date.today().isoformat()
    pilares = "\n".join(f"- {p}" for p in cfg.pilares)
    usados = "\n".join(f"- {t}" for t in temas_usados) or "- (nenhum ainda)"
    recentes = ", ".join(pilares_usados) or "nenhum"

    if tema:
        tarefa = f"O tema de hoje já foi definido: {tema}. Pesquise esse tema."
    else:
        tarefa = (
            "Escolha UM tema específico e interessante para o post de hoje. Prefira um pilar "
            f"diferente dos usados recentemente ({recentes}). Datas comemorativas, aniversários "
            "de autores ou lançamentos relevantes desta semana são bons ganchos, se houver."
        )

    prompt = f"""Você é o pesquisador de um perfil de Instagram. Hoje é {hoje}.

{_perfil(cfg)}

Pilares de conteúdo:
{pilares}

Temas já publicados (não repita nem faça variações muito próximas):
{usados}

{tarefa}

Use a busca na web para confirmar cada fato em fontes confiáveis (editoras, enciclopédias,
universidades, jornais reconhecidos). Descarte o que não conseguir confirmar, inclusive
citações de autoria duvidosa.

Responda com um dossiê em texto simples contendo:
1. TEMA: o tema escolhido, em uma linha
2. PILAR: o pilar atendido (copie o texto do pilar)
3. ÂNGULO: por que isso prende a atenção do público
4. FATOS: de 5 a 10 fatos verificados, cada um com a URL da fonte
5. CUIDADOS: mitos comuns ou pontos controversos que o redator deve evitar"""

    cliente = _cliente()
    mensagens: list[dict] = [{"role": "user", "content": prompt}]
    ferramentas = [{
        "type": "web_search_20260209",
        "name": "web_search",
        "max_uses": int(cfg.ia.get("buscas_maximas", 8)),
    }]

    for _ in range(MAX_CONTINUACOES + 1):
        resposta = cliente.beta.messages.create(
            model=cfg.ia.get("modelo", "claude-opus-5-5"),
            max_tokens=16000,
            output_config={"effort": cfg.ia.get("esforco_pesquisa", "medium")},
            tools=ferramentas,
            messages=mensagens,
            betas=BETAS,
            fallbacks="default",
        )
        if resposta.stop_reason != "pause_turn":
            break
        # A busca no servidor pausou no meio; reenviar a conversa faz ela continuar.
        mensagens = [mensagens[0], {"role": "assistant", "content": resposta.content}]
    else:
        raise ErroIA("A pesquisa não terminou após várias continuações.")

    _checar_parada(resposta)
    dossie = _texto(resposta)
    if not dossie:
        raise ErroIA("A pesquisa voltou vazia.")
    log.info("Pesquisa concluída (%s tokens de saída).", resposta.usage.output_tokens)
    return dossie


def redigir(cfg: Config, dossie: str) -> Post:
    """Transforma o dossiê em um carrossel pronto (capa, slides, legenda e hashtags)."""
    regras = "\n".join(f"- {r}" for r in cfg.regras)
    minimo = cfg.post.get("slides_minimo", 3)
    maximo = cfg.post.get("slides_maximo", 6)

    prompt = f"""Você é o redator de um perfil de Instagram e vai criar um post em carrossel.

{_perfil(cfg)}

Regras do perfil:
{regras}

Formato:
- Capa com um gancho forte (titulo_capa) e um subtítulo que complementa.
- De {minimo} a {maximo} slides de conteúdo; cada slide traz uma ideia só, com título curto e
  texto de no máximo ~260 caracteres. Os slides precisam ser lidos em sequência, como uma história.
- chamada_final convida a salvar o post, comentar ou seguir o perfil.
- A legenda aprofunda um pouco o assunto (3 a 6 parágrafos curtos), sem repetir os slides
  palavra por palavra, e não leva hashtags (elas vão no campo hashtags).
- prompt_imagem descreve, em inglês, uma ilustração para o fundo da capa (sem texto e sem
  rostos de pessoas reais); o título será escrito por cima, então deixe espaço "respirando".
- Use apenas os fatos do dossiê abaixo. Em "fontes", liste as URLs que você usou.

Dossiê da pesquisa:
<dossie>
{dossie}
</dossie>"""

    resposta = _cliente().beta.messages.parse(
        model=cfg.ia.get("modelo", "claude-opus-5-5"),
        max_tokens=16000,
        output_config={"effort": cfg.ia.get("esforco_redacao", "medium")},
        output_format=Post,
        messages=[{"role": "user", "content": prompt}],
        betas=BETAS,
        fallbacks="default",
    )
    _checar_parada(resposta)
    post = resposta.parsed_output
    if post is None:
        raise ErroIA("A IA não devolveu um post no formato esperado.")
    if len(post.slides) > maximo:
        post.slides = post.slides[:maximo]
    if len(post.slides) < 1:
        raise ErroIA("O post veio sem slides de conteúdo.")
    return post
