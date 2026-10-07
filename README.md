# Assistente automático do Mapa das Ideias 📚

Assistente que todos os dias **pesquisa**, **escreve**, **gera as imagens** e **publica no
Instagram** os posts do [@mapadasideias_](https://www.instagram.com/mapadasideias_), seguindo o
*Guia de Marca e Produção*:

| Horário (Brasília) | Formato | O que é |
|---|---|---|
| 09:53 | **Carrossel de 7 slides** | capa com pergunta concreta → contexto → desenvolvimento → resposta → reflexão → leituras e aplicação → CTA |
| 18:47 | **Imagem avulsa** | curiosidade, comparação ou reflexão independente do carrossel |

Os horários vêm dos melhores horários que o Metricool identificou (10h e 18h–19h).

```
 Pesquisa ──▶ Redação ──▶ Revisão ──▶ Imagens ──▶ Slides ──▶ Hospedagem ──▶ Instagram
 Claude +     Claude      Claude      IA (cena)   layout da    ImgBB          Graph API
 busca web    (JSON)      checklist   + capa real  marca
                                       do livro    (Pillow)
```

- **Pesquisa**: escolhe a pauta mantendo os pilares em equilíbrio, priorizando livros conhecidos e
  evitando temas já feitos (o histórico já inclui os 18 posts que você produziu). Confirma cada
  fato na web e guarda as fontes; separa o que é da obra, o que é interpretação e o que é aplicação.
- **Redação**: segue a estrutura de 7 slides do guia, ganchos em forma de pergunta concreta,
  CTA único no fim (nunca "arraste"), legenda com pergunta e poucas hashtags.
- **Revisão**: uma segunda passada confere fatos contra o dossiê, citações, ortografia,
  promessa da capa x resposta e CTA, antes de qualquer imagem ser gerada.
- **Mundo visual**: cada post escolhe uma técnica do cardápio do guia (óleo renascentista,
  aquarela, xilogravura, noir, risografia...) que combine com o livro e que não tenha aparecido
  recentemente. Os prompts seguem o padrão "nível Sherlock Holmes".
- **Layout fixo da marca**: etiqueta coral no topo, título Montserrat com palavras em coral,
  texto de apoio, cena na metade de baixo, `n/7` no canto inferior direito e o logo original no
  canto inferior esquerdo. Em fundos claros (aquarela, vetor), o texto vira azul-marinho sozinho.
- **Capa real do livro**: no slide 1, pelo ISBN de uma edição verificável (Open Library / Google
  Books, ou uma foto sua em `marca/capas/<ISBN>.jpg`). Se não achar, sai sem capa, nunca inventada.

Cada post fica em `posts/<data>_<formato>_<tema>/` com `dossie.md` (pesquisa e fontes),
`post.json`, `legenda.txt`, `prompts_imagens.md` (os prompts de cada slide, para refazer no
ChatGPT se quiser) e, depois de publicado, `publicacao.json` com o link.

---

## Configuração (uma vez só)

### 1. Instagram

A API oficial só publica em contas **Profissionais** (Criador de conteúdo ou Empresa).

1. Crie um app em <https://developers.facebook.com/apps> (tipo **Empresa**) e adicione o produto
   **Instagram** → *API com login do Instagram*.
2. Em *Gerar tokens de acesso*, conecte o @mapadasideias_ e gere o token. Anote o **token**
   (`IG_ACCESS_TOKEN`) e o **ID da conta** (`IG_USER_ID`).

> ⚠️ **O token expira em 60 dias.** Renove antes (no mesmo painel, ou com
> `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=SEU_TOKEN`)
> e atualize o segredo. Se preferir o caminho pelo Facebook (Página + Gerenciador de Negócios),
> troque `graph_host` para `https://graph.facebook.com` no `config.yaml`.

### 2. Chaves

| Segredo | Para quê | Onde conseguir | Custo |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | pesquisa, redação e revisão | <https://console.anthropic.com> | pago por uso |
| `IG_USER_ID` e `IG_ACCESS_TOKEN` | publicar | passo 1 | grátis |
| `IMGBB_API_KEY` | link público das imagens | <https://api.imgbb.com> | grátis |
| `POLLINATIONS_TOKEN` | **imagens com modelo bom** | <https://enter.pollinations.ai/keys> | créditos grátis; modelos melhores consomem "pollen" |
| `GOOGLE_BOOKS_API_KEY` *(opcional)* | achar a capa real pelo ISBN | Google Cloud → APIs → Books API | grátis |
| `OPENAI_API_KEY` *(opcional)* | imagens com a IA do ChatGPT (`provedor: openai`) | <https://platform.openai.com> | pago por imagem |

> **Sobre as imagens:** sem `POLLINATIONS_TOKEN`, o Pollinations só oferece um modelo antigo e
> fraco, que ignora técnicas como aquarela e risografia. Com a chave gratuita, o assistente usa o
> modelo `zimage` (troque em `imagens_ia.pollinations_modelo`). Para chegar perto da qualidade que
> você tem hoje no ChatGPT, use `provedor: openai` (pago por imagem; a assinatura do ChatGPT Plus
> não inclui a API).

### 3. Cadastrar os segredos no GitHub

**Settings → Secrets and variables → Actions → New repository secret**, um para cada chave.

### 4. Ligar

Os agendamentos do GitHub só rodam no branch padrão (`main`): faça o merge deste código lá.

**Primeiro teste**: **Actions → Post automático no Instagram → Run workflow**, escolha o formato
e **desmarque "Publicar"**. As imagens ficam em *Artifacts* na página da execução. Aprovou? Rode de
novo com "Publicar" marcado.

---

## Ajustes no `config.yaml`

- `perfil`, `pilares`, `preferencias_de_pauta`, `regras`: linha editorial do guia.
- `visual`: cores, fontes e logo (identidade fixa).
- `mundos_visuais`: o cardápio de técnicas, com quando usar cada uma.
- `ia.revisao`: liga/desliga a etapa de revisão.
- Horários: em `.github/workflows/instagram.yml` (linhas `cron`, em UTC).

## Rodando no computador

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...  POLLINATIONS_TOKEN=...

python -m assistente gerar                                  # carrossel, sem publicar
python -m assistente gerar --formato imagem                 # imagem avulsa
python -m assistente gerar --tema "Drácula, de Bram Stoker"  # força um tema
python -m assistente publicar posts/<pasta>                 # publica um post já criado
```

Dá para editar `legenda.txt` antes de publicar: o comando `publicar` usa o que estiver no arquivo.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Estrutura

```
assistente/
  ia.py               pesquisa (busca na web), redação e revisão com o Claude
  modelos.py          formato do post, destaques em coral e legenda
  geracao_imagens.py  cenas por IA (pollinations, cloudflare, openai, gemini)
  capas.py            capa real do livro pelo ISBN
  imagens.py          layout fixo da marca (Pillow)
  hospedagem.py       upload das imagens (ImgBB ou GitHub)
  instagram.py        publicação pela Instagram Graph API
  historico.py        histórico de temas e mundos visuais
  pipeline.py         junta tudo
config.yaml           marca, linha editorial, mundos visuais e opções
marca/logo.png        logo original (recortado no círculo)
marca/capas/          fotos de capas de edições reais, nomeadas pelo ISBN (opcional)
fontes/               Montserrat (licença OFL)
data/historico.json   histórico de posts
posts/                posts gerados
```

## Limites conhecidos

- As IAs de imagem gratuitas não escrevem texto em português direito; por isso os textos,
  setas e etiquetas são desenhados pelo assistente por cima da cena.
- A API do Instagram não adiciona música a posts de imagem/carrossel.
- O assistente publica sozinho, sem revisão humana. Para revisar antes, rode o workflow com
  "Publicar" desmarcado e publique depois com `python -m assistente publicar`.
