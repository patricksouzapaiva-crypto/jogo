"""Pesquisa (com busca na web), redação e revisão do post usando o Claude."""

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


def _lista(itens) -> str:
    return "\n".join(f"- {i}" for i in itens) or "- (nenhum)"


def _perfil(cfg: Config) -> str:
    p = cfg.perfil
    return (
        f"Perfil: {p.get('nome', '')} ({p.get('arroba', '')})\n"
        f"Promessa editorial: {p.get('promessa', '')}\n"
        f"Idioma: {p.get('idioma', 'português do Brasil')}\n"
        f"Público: {str(p.get('publico', '')).strip()}\n"
        f"Tom: {str(p.get('tom_de_voz', '')).strip()}\n\n"
        f"Regras de conteúdo (obrigatórias):\n{_lista(cfg.regras)}"
    )


TAREFA_POR_FORMATO = {
    "carrossel": (
        "O post de hoje é um CARROSSEL de 7 slides sobre um livro (ou obra, mito, ideia) que "
        "responde a uma pergunta concreta e intrigante sobre ele."
    ),
    "imagem": (
        "O post de hoje é uma IMAGEM AVULSA, independente de qualquer carrossel: uma curiosidade, "
        "comparação ou reflexão sobre um livro ou autor conhecido, que se entenda em poucos "
        "segundos (ex.: 'O autor de Alice no País das Maravilhas era professor de matemática')."
    ),
}


def pesquisar(cfg: Config, temas_usados: list[str], pilares_usados: list[str],
              tema: str | None = None, formato: str = "carrossel") -> str:
    """Escolhe um tema (se não for informado) e monta um dossiê com fatos verificados na web."""
    hoje = dt.date.today().isoformat()
    preferencias = cfg.dados.get("preferencias_de_pauta") or []

    if tema:
        tarefa = f"O tema já foi definido: {tema}. Pesquise esse tema."
    else:
        tarefa = (
            "Escolha UM tema. Mantenha os pilares em equilíbrio: prefira um pilar diferente dos "
            f"usados recentemente ({', '.join(pilares_usados) or 'nenhum'}). Se usar um gancho de "
            "atualidade (data comemorativa, lançamento, adaptação), confirme a fonte e a data reais; "
            "nunca afirme que algo está viralizando sem evidência."
        )

    prompt = f"""Você é o pesquisador de um perfil de Instagram sobre livros e ideias. Hoje é {hoje}.

{_perfil(cfg)}

Pilares (em equilíbrio deliberado):
{_lista(cfg.pilares)}

Preferências de pauta:
{_lista(preferencias)}

Temas já publicados (não repita nem faça variações muito próximas):
{_lista(temas_usados)}

{TAREFA_POR_FORMATO[formato]}

{tarefa}

Use a busca na web para confirmar cada informação em fontes confiáveis (editoras, enciclopédias,
universidades, jornais reconhecidos). Descarte o que não conseguir confirmar.

Responda com um dossiê em texto simples contendo:
1. TEMA: o tema escolhido, em uma linha (livro + autor quando houver)
2. PILAR: o pilar atendido (copie o texto do pilar)
3. PERGUNTA: a pergunta concreta que o post vai responder
4. NA OBRA: o que de fato acontece no livro / o que o autor escreveu, com fontes
5. FATOS: de 5 a 10 fatos verificados (datas, contexto, curiosidades), cada um com a URL da fonte
6. CITAÇÕES: só citações literais verificadas, com autor, obra e a URL; deixe vazio se não houver
7. INTERPRETAÇÕES: leituras conhecidas da obra, dizendo de quem são
8. SPOILERS: o que seria spoiler relevante
9. EDIÇÃO: se o tema for um livro específico, o ISBN-13 de uma edição brasileira identificável
   (editora e ano) com a URL onde você o confirmou; deixe vazio se não confirmar
10. CUIDADOS: mitos comuns ou pontos controversos a evitar"""

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


def _estrutura(cfg: Config, formato: str) -> tuple[str, int]:
    if formato == "imagem":
        rotulo = cfg.formatos.get("imagem", {}).get("rotulo", "CURIOSIDADE LITERÁRIA")
        return f"""IMAGEM AVULSA (exatamente 1 slide):
- rotulo: "{rotulo}" (ou COMPARAÇÃO / REFLEXÃO, se for o caso).
- titulo: a curiosidade em até ~70 caracteres, que funcione sozinha como gancho.
- texto: 1 a 2 frases (até ~170 caracteres) que explicam com data, nome ou número.
- Pode usar diagrama_de/diagrama_para quando houver uma virada clara (ex.: 1893 → 1903).
- citacao, autor_citacao e isbn_capa ficam vazios.""", 1

    total = int(cfg.formatos.get("carrossel", {}).get("total_slides", 7))
    return f"""CARROSSEL com exatamente {total} slides, nesta estrutura:
1) Capa: tema identificável e abertura forte. rotulo com obra e autor (ex.: "BRAM STOKER • DRÁCULA").
   titulo é uma PERGUNTA CONCRETA, não um anúncio. Ex.: não "Lições de O Pequeno Príncipe sobre
   vínculos", e sim "Se existiam tantas rosas, por que a dele era *especial?*". texto é um
   subtítulo curto. citacao só se for literal e estiver no dossiê.
2) Contexto: por que a pergunta importa.
3) Desenvolvimento: descobertas e exemplos (o que acontece na obra).
4) Resposta: cumpre a promessa da capa.
5) Reflexão ou aplicação.
6) Leituras e nossa aplicação, SEMPRE separadas e rotuladas (ex.: rotulo "LEITURA" para a
   interpretação de alguém, rotulo "NA PRÁTICA" para a aplicação proposta por nós).
7) Conclusão com UM único CTA bem visível, coerente com o conteúdo: seguir (com um benefício
   concreto), comentar uma experiência ou compartilhar uma reflexão. Nunca "arraste" nem
   "próximo slide"; não acumule pedidos.
Nos slides 2 a 6: rotulo situa o assunto; titulo até ~70 caracteres; texto de 1 a 2 frases
(até ~170 caracteres). Use diagrama_de/diagrama_para/diagrama_legenda no máximo uma vez, quando
um esquema simples ajudar (ex.: ERRO → SOFRIMENTO).
isbn_capa: o ISBN da seção EDIÇÃO do dossiê, se houver; senão vazio.""", total


def _orientacoes_comuns(cfg: Config, mundos_recentes: list[str]) -> str:
    mundos = cfg.secao("mundos_visuais")
    cardapio = "\n".join(
        f"- {nome}: combina com {dados.get('combina', '')}" for nome, dados in mundos.items()
    )
    return f"""Escrita:
- Marque entre *asteriscos* de 1 a 3 palavras do titulo que aparecem em coral; é a palavra que
  dá o "soco" da frase (ex.: "Dez anos depois, ele *voltou.*"). Campos que não se aplicam ficam "".
- Pouco texto por slide: o visual é uma imagem em tela cheia com o texto por cima.
- Ao falar da obra, deixe claro o que é da obra, o que é interpretação (de quem) e o que é
  aplicação proposta por nós. Avise antes de spoilers relevantes.

Mundo visual (mundo_visual): escolha UM do cardápio para o post inteiro, o que melhor carrega o
"mundo" do livro, evitando os usados recentemente ({', '.join(mundos_recentes) or 'nenhum'}):
{cardapio}

prompt_imagem (em inglês), um por slide, no padrão mais completo ("nível Sherlock Holmes"):
direção de arte e fotográfica profissional em 60 a 120 palavras, com: técnica/meio do mundo
escolhido; cena e objetos concretos ligados ao que o slide diz (época, lugar, figurino);
lente e enquadramento; iluminação e temperatura de luz; paleta; composição com a metade de
cima calma para o texto e o assunto na metade de baixo; restrições (sem texto, letras, placas
ou logos). Todos os slides devem parecer do mesmo carrossel. Pessoas históricas aparecem como
estátuas, silhuetas ou de costas, nunca como retrato realista do rosto.

Legenda:
- Abre com uma frase que desperta interesse e não repete a arte.
- Acrescenta contexto em parágrafos curtos, com título, autor e palavras-chave naturais.
- Termina com uma pergunta específica, quando fizer sentido. Sem hashtags na legenda.
- hashtags: poucas e pertinentes (até 6).
- fontes: as URLs do dossiê que você usou."""


def _parse(cfg: Config, prompt: str, esforco: str) -> Post:
    resposta = _cliente().beta.messages.parse(
        model=cfg.ia.get("modelo", "claude-opus-5-5"),
        max_tokens=16000,
        output_config={"effort": esforco},
        output_format=Post,
        messages=[{"role": "user", "content": prompt}],
        betas=BETAS,
        fallbacks="default",
    )
    _checar_parada(resposta)
    if resposta.parsed_output is None:
        raise ErroIA("A IA não devolveu um post no formato esperado.")
    return resposta.parsed_output


def _normalizar(cfg: Config, post: Post, formato: str, total: int) -> Post:
    if not post.slides:
        raise ErroIA("O post veio sem slides.")
    if len(post.slides) > total:  # mantém a capa e o slide final
        post.slides = post.slides[: total - 1] + post.slides[-1:] if total > 1 else post.slides[:1]
    if formato == "carrossel" and len(post.slides) < 3:
        raise ErroIA(f"O carrossel veio com só {len(post.slides)} slides.")
    mundos = cfg.secao("mundos_visuais")
    if post.mundo_visual not in mundos and mundos:
        post.mundo_visual = next(iter(mundos))
    return post


def redigir(cfg: Config, dossie: str, formato: str = "carrossel",
            mundos_recentes: list[str] | None = None) -> Post:
    """Transforma o dossiê em um post pronto (slides, legenda e hashtags)."""
    estrutura, total = _estrutura(cfg, formato)
    prompt = f"""Você é o redator e diretor de arte de um perfil de Instagram sobre livros e ideias.

{_perfil(cfg)}

{estrutura}

{_orientacoes_comuns(cfg, mundos_recentes or [])}

Use apenas o que está no dossiê abaixo.

<dossie>
{dossie}
</dossie>"""
    post = _parse(cfg, prompt, cfg.ia.get("esforco_redacao", "high"))
    return _normalizar(cfg, post, formato, total)


def revisar(cfg: Config, dossie: str, post: Post, formato: str = "carrossel",
            mundos_recentes: list[str] | None = None) -> Post:
    """Checagem antes de finalizar: conteúdo, ortografia, promessa da capa e CTA."""
    estrutura, total = _estrutura(cfg, formato)
    prompt = f"""Você é o editor-chefe de um perfil de Instagram sobre livros e ideias e vai revisar
um post antes da publicação automática (não haverá revisão humana).

{_perfil(cfg)}

O post deveria seguir:
{estrutura}

{_orientacoes_comuns(cfg, mundos_recentes or [])}

Checklist:
1. Cada fato, data, número e citação está no dossiê? Remova ou corrija o que não estiver.
   Citação sem fonte literal no dossiê sai.
2. Interpretação nunca aparece como se fosse frase do autor; obra / interpretação / aplicação
   estão separadas e rotuladas.
3. Ortografia e gramática do português do Brasil impecáveis; marcação *destaque* correta.
4. A capa faz uma pergunta concreta e o slide de resposta cumpre essa promessa.
5. O último slide tem um único CTA, sem "arraste"/"próximo slide".
6. Spoilers relevantes estão sinalizados.
7. Os prompt_imagem são completos e coerentes entre si e com o mundo visual.

Devolva o post inteiro já corrigido (se estiver tudo certo, devolva igual).

<dossie>
{dossie}
</dossie>

<post>
{post.model_dump_json(indent=2)}
</post>"""
    revisado = _parse(cfg, prompt, cfg.ia.get("esforco_redacao", "high"))
    return _normalizar(cfg, revisado, formato, total)
