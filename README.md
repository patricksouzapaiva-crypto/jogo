# Assistente automático de Instagram 📚

Um assistente que, todos os dias, **pesquisa** um tema sobre livros, filosofia, literatura e
conhecimentos gerais, **escreve** um carrossel com legenda e hashtags, **gera as imagens** (com
ilustração de capa feita por IA) e **publica no Instagram**, tudo sem intervenção.

```
 ┌───────────┐   ┌───────────┐   ┌──────────────────┐   ┌────────────┐   ┌───────────┐
 │ Pesquisa  │──▶│ Redação   │──▶│ Imagens          │──▶│ Hospedagem │──▶│ Instagram │
 │ Claude +  │   │ Claude    │   │ capa com IA +    │   │ ImgBB      │   │ Graph API │
 │ busca web │   │ (JSON)    │   │ slides (Pillow)  │   │            │   │ carrossel │
 └───────────┘   └───────────┘   └──────────────────┘   └────────────┘   └───────────┘
        ▲                                                                       │
        └──────────── histórico (data/historico.json) evita repetir temas ◀─────┘
```

- **Pesquisa**: o Claude escolhe um tema (alternando entre os pilares de conteúdo e evitando temas
  já publicados) e confirma cada fato na web, guardando as fontes.
- **Redação**: transforma a pesquisa em capa + 3 a 6 slides + chamada final + legenda + hashtags.
- **Imagens**: a capa ganha uma ilustração gerada por IA (Pollinations grátis, Cloudflare, OpenAI
  ou Gemini) com o título escrito por cima; os demais slides seguem um visual de "página de livro".
- **Publicação**: as imagens vão para o ImgBB (link público) e o post é publicado pela API oficial
  do Instagram.
- **Agendamento**: o GitHub Actions roda tudo uma vez por dia, sem servidor.

Cada post fica salvo em `posts/<data>_<tema>/` com o dossiê da pesquisa (`dossie.md`), o conteúdo
(`post.json`), a legenda (`legenda.txt`) e, depois de publicado, o link (`publicacao.json`).

---

## Configuração (uma vez só)

### 1. Conta do Instagram

A API oficial só publica em contas **Profissionais** (Criador de conteúdo ou Empresa).

1. No app do Instagram: *Configurações → Tipo de conta e ferramentas → Mudar para conta profissional*.
2. Crie um app em <https://developers.facebook.com/apps> (tipo **Empresa**) e adicione o produto
   **Instagram** → *API com login do Instagram*.
3. Em *Gerar tokens de acesso*, conecte sua conta do Instagram e gere o token. Anote:
   - o **token de acesso** → vai virar o segredo `IG_ACCESS_TOKEN`;
   - o **ID da conta do Instagram** (número que aparece ao lado da conta) → `IG_USER_ID`.
4. Como esse token é do "Instagram Login", troque no `config.yaml`:
   ```yaml
   publicacao:
     graph_host: "https://graph.instagram.com"
   ```
   (Se você usar o caminho antigo, com conta do Instagram ligada a uma Página do Facebook e token
   do Facebook, deixe `https://graph.facebook.com`.)

> ⚠️ **O token expira em 60 dias.** Renove antes disso (no mesmo painel, ou com
> `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=SEU_TOKEN`)
> e atualize o segredo `IG_ACCESS_TOKEN`. Com o caminho do Facebook, um token de **Usuário do
> Sistema** do Gerenciador de Negócios não expira.

### 2. Chaves de API

| Segredo | Para quê | Onde conseguir | Custo |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | pesquisa e redação | <https://console.anthropic.com> → API Keys | pago por uso |
| `IG_USER_ID` | publicar | passo 1 | grátis |
| `IG_ACCESS_TOKEN` | publicar | passo 1 | grátis |
| `IMGBB_API_KEY` | hospedar as imagens | <https://api.imgbb.com> | grátis |
| `POLLINATIONS_TOKEN` *(opcional)* | mais limite e sem marca d'água | site do Pollinations (<https://pollinations.ai>) | grátis |
| `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` *(opcional)* | imagens com o provedor `cloudflare` | painel da Cloudflare → Workers AI | grátis até a cota diária |
| `OPENAI_API_KEY` *(opcional)* | imagens com o provedor `openai` | <https://platform.openai.com> | pago por imagem |
| `GEMINI_API_KEY` *(opcional)* | imagens com o provedor `gemini` | <https://aistudio.google.com> | conforme o plano |

> A assinatura do ChatGPT Plus **não** inclui acesso à API: para usar o provedor `openai` é
> preciso colocar créditos em platform.openai.com. O Google **Flow** não tem API pública, por isso
> não dá para automatizá-lo; para imagens do Google use o provedor `gemini`.

### 3. Cadastrar os segredos no GitHub

No repositório: **Settings → Secrets and variables → Actions → New repository secret**, e crie um
segredo para cada chave da tabela acima (no mínimo os quatro primeiros + `IMGBB_API_KEY`).

### 4. Ajustar o perfil

Edite o [`config.yaml`](config.yaml): seu `@`, nome do perfil, tom de voz, pilares de conteúdo,
cores, quantidade de slides, hashtags fixas e o provedor de imagens.

### 5. Ligar o agendamento

O workflow [`.github/workflows/instagram.yml`](.github/workflows/instagram.yml) roda todo dia às
**08:47 (horário de Brasília)**. Agendamentos do GitHub só valem no branch padrão (`main`), então
faça o merge deste código no `main`. Para mudar o horário, edite a linha `cron` (em UTC).

**Primeiro teste**: vá em **Actions → Post automático no Instagram → Run workflow**, desmarque
"Publicar no Instagram" e rode. As imagens ficam disponíveis em *Artifacts* na página da execução.
Gostou? Rode de novo com a opção marcada para publicar de verdade.

---

## Rodando no seu computador

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # no Windows: set ANTHROPIC_API_KEY=...

python -m assistente gerar                        # pesquisa e cria (sem publicar)
python -m assistente gerar --tema "Os estoicos"   # força um tema
python -m assistente publicar posts/<pasta>       # publica um post já criado
python -m assistente rodar                        # tudo de uma vez
```

Você pode editar `legenda.txt` antes de publicar: o comando `publicar` usa o que estiver no arquivo.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Estrutura

```
assistente/
  ia.py               pesquisa com busca na web e redação (Claude)
  modelos.py          formato do post e montagem da legenda
  geracao_imagens.py  ilustração da capa por IA (pollinations, cloudflare, openai, gemini)
  imagens.py          desenho dos slides (Pillow)
  hospedagem.py       upload das imagens (ImgBB ou GitHub)
  instagram.py        publicação pela Instagram Graph API
  historico.py        registro dos posts para não repetir temas
  pipeline.py         junta tudo
config.yaml           perfil, pilares, visual e opções
data/historico.json   histórico de posts
posts/                posts gerados
```

## Bom saber

- **Fatos e fontes**: a IA só usa fatos confirmados na busca, e o dossiê com as fontes fica salvo em
  cada post. Mesmo assim, vale passar o olho de vez em quando.
- **Custo da IA**: cada post faz uma pesquisa com algumas buscas na web e uma redação. Para gastar
  menos, reduza `buscas_maximas` ou use `esforco_*: "low"` no `config.yaml`.
- **Se a ilustração falhar**, a capa sai só com tipografia e o post é publicado do mesmo jeito.
- **Limites do Instagram**: até 10 imagens por carrossel, 30 hashtags e 2.200 caracteres na legenda,
  e o assistente já respeita todos eles.
