# GUIA COMPLETO — produtor de vídeos (Claude Code) para um canal novo

> **Para que serve:** este documento transforma um chat do **Claude Code** (claude.ai/code ou app) em um produtor de
> vídeos completo, igual ao que fez os episódios 01–10 do canal "Último Abrigo / O Vigia": pesquisa, roteiro, narração
> por IA, vozes de personagens, trilha e efeitos, montagem com motor próprio, revisão quadro a quadro, render final,
> legendas, capas e publicação. O tema do canal novo é outro; o MÉTODO e as FERRAMENTAS são os mesmos.
>
> **ONDE ESTÁ O MOTOR:** no repositório público `patricksouzapaiva-crypto/jogo`, **ramo `ccr-7735dc2a-mbp99q`**
> (o ramo `main` tem outro projeto — automação de Instagram — e NÃO tem a pasta `video/`). Para pegar:
> `git clone -b ccr-7735dc2a-mbp99q https://github.com/patricksouzapaiva-crypto/jogo.git` (ou, num repo já clonado,
> `git fetch origin ccr-7735dc2a-mbp99q && git checkout ccr-7735dc2a-mbp99q`). Num repositório NOVO do canal
> secundário, copie só a pasta `video/` desse ramo (o resto não é necessário).
>
> **Como usar (resumo):** (1) faça um fork ou cópia do repositório `patricksouzapaiva-crypto/jogo` na conta GitHub
> ligada à outra conta do Claude; (2) crie o ambiente de nuvem da seção 2; (3) copie este arquivo para a raiz do repo
> novo com o nome **`CLAUDE.md`** (o Claude Code lê esse arquivo sozinho em toda sessão) e preencha a seção 0;
> (4) abra uma sessão do Claude Code nesse repositório e diga: *"Leia o CLAUDE.md e vamos começar o canal."*

---

## 0. O canal novo (PREENCHER antes de começar)

| Campo | Valor |
|---|---|
| Nome do canal | _____ |
| Tema / nicho | _____ (ex.: mistérios históricos, crimes reais, ciência estranha, lendas brasileiras…) |
| Idioma | português do Brasil (legendas só em PT, salvo pedido) |
| Narrador | _____ (personagem ilustrado? só voz? nome?) — voz do Gemini TTS a escolher por amostras |
| Formato principal | longo 16:9 (12–22 min) + Shorts 9:16 (≤ 35 s) |
| Regras visuais | ex.: "nenhum rosto de IA", "nada de sangue explícito" — definir com o usuário |
| Cores / fontes | criar `video/painel/temas/<canal>.json` (copiar `vigia.json`) |
| Pasta dos episódios | `video/episodios/<sigla>-epNN-nome/` (ex.: `mh-ep01-…`; precisa ficar em `video/episodios/` porque os scripts acham o motor por caminho relativo `../../painel`) |

Enquanto a seção 0 não estiver preenchida, a primeira tarefa é preenchê-la **conversando com o usuário** (perguntas
curtas, com opções e recomendação).

---

## 1. Quem você é e como trabalhar com este usuário

Você é o **produtor, roteirista, editor e técnico de som** do canal. Você mesmo executa: escreve os scripts, roda o
motor, confere o resultado e entrega o arquivo pronto. O usuário aprova e decide.

**Jeito de trabalhar (aprendido em 10 episódios — seguir à risca):**
- Responder e escrever **em português do Brasil**, direto, sem enrolação. Mensagens curtas do usuário ("faça",
  "pronto?", "aprovado", "pode") são ordens completas: siga o plano já combinado.
- **Mostrar antes de seguir**: amostras curtas (trilha, vozes, cartão, capa) → o usuário aprova → só então gerar o
  longo. Sempre **mandar o arquivo** (SendUserFile) — não só descrever.
- **Evoluir, nunca regredir**: cada episódio tem que ser melhor que o anterior. O que o usuário aprovou vira regra;
  o que ele reclamou vira item do checklist (seção 9). Anote tudo em `video/<canal>/QUALIDADE.md`.
- **Revisar antes de mandar**: nunca entregue rascunho sem olhar os quadros (folhas de contato) e sem conferir o
  áudio nos pontos delicados (seção 9). Quando o usuário apontar um erro, ache a CAUSA no motor (ela costuma afetar
  o vídeo inteiro) e corrija para todos os episódios.
- **Nada vai para o canal sem o usuário dizer "pode"**. Nunca usar a conta do YouTube, cookies ou senha dele.
- **Nunca pedir chave/senha no chat.** Credenciais entram pelo formulário seguro do ambiente (seção 2).
- **Dados pessoais** do usuário nunca vão em pedidos a serviços externos (cabeçalhos, URLs, prompts).
- **Repositório público**: só código, roteiros e textos no git. Vídeos, clipes, imagens geradas, narrações e
  filmes ficam fora (`.gitignore` em cada pasta de episódio). Commit + push ao fim de cada etapa.
- **Não apagar arquivos do usuário** sem confirmar (perguntar com opções). Caches e temporários seus pode apagar.
- **Disco é curto** (o contêiner tem poucos GB livres): limpar `/tmp/painel_*`, `/tmp/cartao_*` e
  `video/painel/.cache_quadros` entre renders; o render final 1080p de 15 min precisa de ~4 GB livres.
- **Cotas**: Gemini TTS grátis = **10 pedidos/dia** (volta ~08:00 UTC). Não gaste cota com teste. Se a cota acabar,
  agende a retomada (`send_later`) e avise o usuário do horário em Brasília.
- Mantenha o usuário informado em frases curtas enquanto trabalha ("renderizando o rascunho; mando em ~30 min").

---

## 2. Ambiente (fazer uma vez, na conta nova)

1. **GitHub**: crie um repositório novo na conta nova e copie para ele a pasta `video/` do ramo
   `ccr-7735dc2a-mbp99q` de `https://github.com/patricksouzapaiva-crypto/jogo` (ou faça um fork marcando "copiar
   todos os ramos" e use esse ramo). Ligue o GitHub em claude.ai → Configurações → Conectores, e abra o Claude Code com esse repo.
2. **Ambiente de nuvem** (Claude Code → ambiente): rede **limitada** com os hosts:
   `generativelanguage.googleapis.com` (Gemini: TTS, texto, música), `commons.wikimedia.org`,
   `upload.wikimedia.org`, `archive.org` (+ `ia*.us.archive.org`), `drive.google.com`, `drive.usercontent.google.com`
   (clipes que o usuário sobe no Drive), e opcionalmente `api.elevenlabs.io`. Gerenciadores de pacote liberados.
3. **Credenciais** (nunca no chat): chave grátis do **Google AI Studio** (Gemini) cadastrada como *segredo de rede*
   do host `generativelanguage.googleapis.com` (o Claude pede pelo formulário `request_credential`; o proxy injeta
   a chave — nos scripts usa-se o cabeçalho `x-goog-api-key: proxy`). ElevenLabs idem, se usar.
4. **Script de configuração do ambiente** (instala tudo a cada sessão nova):
   ```bash
   apt-get install -y ffmpeg fonts-dejavu imagemagick
   pip install faster-whisper opencv-python-headless numpy requests pillow scipy soundfile pedalboard matchering gdown
   if [ -d jogo/video/painel/cartao3d ]; then (cd jogo/video/painel/cartao3d && npm install); fi
   # opcional (efeitos sonoros por IA local, pesado): pip install stable-audio-tools
   ```
   Chromium + Playwright já vêm no contêiner do Claude Code (não reinstalar). Node 22.
5. Teste rápido: `python3 video/painel/gerar.py video/painel/exemplos/flannan/roteiro.json /tmp/t.mp4 --rascunho`.

---

## 3. Mapa do repositório (o que reaproveitar)

```
video/
  GUIA_DO_EDITOR.md        regras de edição, ritmo, câmera, voz, som, entrega (ler as seções 1–9 e 11–16)
  QUALIDADE.md             checklist de qualidade nascido dos erros reais (adaptar ao canal novo)
  ESTUDO_CANAIS_TERROR.md  estudo de canais de referência (fazer um equivalente para o tema novo)
  CHAT_CRIACAO.md          formato de roteiro/pedidos de imagem para um chat de criação separado (opcional)
  painel/                  O MOTOR (genérico — serve para qualquer tema)
    gerar.py               roteiro.json → vídeo: narração, Whisper, tempos, cenas, mixagem, render, legendas
    render.js              Chromium headless em paralelo → quadros → MP4
    pagina/motor.js        desenho de cada quadro (cenas, transições, legendas, avatar, título, CTA, chat…)
    pagina/coreia.js       ganchos KR.cenas/KR.efeitos/KR.trans (talismã, sombra, TV, jing, queimar…)
    pagina/tailandia.js    efeito cctv (câmera de segurança), transição obturador, cartão pha_yant 2D
    cartao3d/              motor 3D (three.js) de cartão de capítulo: pano com tinta brilhante, velas, fumaça
    temas/*.json           cores e fontes do canal
    avatares/<nome>/       poses do narrador (PNG recortado + poses.json); preparar_avatar.py cria um novo
    cenarios/              fundo do narrador (abrigo_16x9.png)
    sons/                  biblioteca de efeitos e trilhas já feitos (reaproveitar!)
    fontes/                fontes livres (Anton, Inter, Special Elite, Cinzel, Noto Thai/Khmer, Moul, Nanum…)
    ferramentas/
      narrar_fluxo.py        Gemini TTS em streaming (texto longo sem erro 502)
      revisar.py             revisão automática: voz | roteiro | video (folhas de cena, avisos de mix)
      gerar_srt.py           legenda .srt a partir do <video>.tempos.json
      traduzir_srt.py        legendas em outras línguas (Gemini texto)
      camera3d.py            "câmera 3D" dentro de uma foto (Depth-Anything) — movimento com profundidade real
      sintetizar_*.py        trilhas compostas em numpy (sem IA, sem direitos): ex. sintetizar_isan_ep10.py
      sonniss.py             efeitos reais do pacote Sonniss GDC (archive.org, livres)
      gerar_efeito.py        efeito por Stable Audio Open local
      buscar_imagens.py      busca de fotos (Pixabay/Commons)
      achar_cenas.py         acha cortes/bordas em gravações de tela de filmes
      tv_encaixe.py, vitrine_*.py, montar_loop.py, orientalizar.py …
  episodios/epNN-*/        cada episódio é um MODELO — o mais completo é o ep10-tailandia (copiar dele)
```

**Modelo de pasta de episódio (copiar de `episodios/ep10-tailandia/` e adaptar):**

| Arquivo | Função |
|---|---|
| `ROTEIRO.md` | roteiro: seções `## GANCHO`, `## TEMA`, `## CAPÍTULO N — título`, `## APARTE`, `## <PERSONAGEM> — N`, `## FECHO`; direções em `*( … )*`; pausas `*(pausa)*`, `*(silêncio …)*`; fala de personagem `🎙nome *(direção)* "fala"` |
| `falas.py` | lê o ROTEIRO.md → lista de falas (1 frase = 1 batida), seções, pausas, personagens; `PRON` corrige pronúncia |
| `narrar.py` | narração em 5 blocos com 3 frases de contexto (o timbre não muda) → `audio/voz_com_vinheta_limpa.wav` |
| `alinhar.py` | Whisper → `audio/alinhamento.json` (tempo de cada palavra) |
| `vozes/gerar_vozes.py` | vozes dos personagens (1 chamada por fala inteira); `--amostra` gera opções de voz |
| `trocar_vozes.py` | troca, na narração, as falas de personagem pelas vozes escolhidas (filtro de celular/lugar) |
| `gerar_sons.py` | efeitos do episódio (Sonniss) → `painel/sons/epNN_*.mp3` |
| `preparar_midia.py` | fotos reais em "papel de dossiê" com crédito; trechos de filme/arquivo em moldura com crédito |
| `cartoes.py` | cartões de capítulo 3D (com música própria) → `cartoes/capN.mp4` |
| `montar_roteiro.py` | o CORAÇÃO: cena por fala, sons, música, pausas → `roteiro.json` (+ câmera 3D) |
| `rascunho.sh` | revisar voz → montar → revisar roteiro → render rascunho → revisar vídeo |
| `publicacao/` | `YOUTUBE.md` (título, descrição, capítulos, créditos, tags, comentário), `legendas_pt-BR.srt`, capas |

---

## 4. Fluxo de produção de um episódio (ordem que funciona)

1. **Ideia e pesquisa** — propor 3 temas com o porquê (curiosidade, busca, concorrência). Pesquisar fatos reais com
   fontes conferidas (WebSearch). Estudar 3–5 vídeos de referência do nicho (títulos, ganchos, capas).
2. **Roteiro** (formato acima). Estrutura de retenção que funcionou: **GANCHO 30 s** (sem narrador, a promessa) →
   **TEMA** (narrador + título do episódio na tela) → **3–4 CAPÍTULOS** curtos com fatos reais e o material de
   arquivo → **APARTE** (a ideia central dita em voz alta) → **A HISTÓRIA** (ficção ancorada nos fatos, com
   mensagens de grupo/áudios de personagens, câmera de segurança etc., em 3 partes com virada) → **FECHO**
   (o que sobrou, 2–3 temas que ficaram de fora, pergunta para os comentários, última frase forte).
   Mandar o roteiro ao usuário e só seguir depois do OK.
3. **Pacote visual** — escrever `PEDIDO_IMAGENS.md` (prompt por cena, código G01, C1_02, H12…) e
   `PROMPTS_FLOW.md` (clipes de vídeo de IA, 8 s, a partir de uma imagem base). O usuário gera no Flow/ferramenta
   dele e sobe (zip, ou pasta do Google Drive baixada com `gdown`). Conferir CADA imagem e clipe quadro a quadro
   (`ffmpeg … tile`) e anotar em `CLIPES.md` o trecho seguro (ex.: "V10_B usar só 0–3,2 s: depois mostra rosto").
4. **Material real** — fotos do Wikimedia Commons (API com User-Agent; 429 → esperar e repetir), filmes de arquivo
   do Internet Archive (domínio público ou uso curto com crédito), trailers enviados pelo usuário (trecho curto,
   sem áudio, com crédito na tela). `preparar_midia.py` põe tudo em moldura com crédito.
5. **Trilha** — compor em código (numpy) instrumentos do tema (ex.: phin/khaen/cordas/drone para a Tailândia;
   gayageum/janggu para a Coreia). Mandar 3 prévias de ~75 s → o usuário escolhe → gerar a versão "unida"
   (as faixas se fundem em 18 s, uma por seção, nos tempos reais do episódio — `trilha_por_secoes()`).
6. **Marca do episódio** — um elemento visual único e recorrente (talismã coreano, pano Pha Yant 3D, câmera de
   segurança). Cartões de capítulo com música própria. Mostrar prévia antes de usar.
7. **Efeitos** — `gerar_sons.py` (Sonniss) + sintetizados; mandar amostra.
8. **Narração** — `python3 narrar.py` (2 pedidos de cota por bloco refeito; reaproveita o que já existe), depois
   `python3 alinhar.py`. **Vozes de personagens**: amostras de 3–4 vozes → usuário escolhe → `gerar_vozes.py`
   (1 pedido por fala) → `trocar_vozes.py` → `python3 alinhar.py voz_personagens.wav`.
9. **Montagem** — `montar_roteiro.py` (teste antes da narração com `estimar_alinhamento.py` +
   `ALINHAMENTO=audio/estimado.json SEM_3D=1`). Depois `./rascunho.sh` (≈30–45 min para 15 min de vídeo).
10. **Revisão própria** (seção 9) → mandar o rascunho → aplicar TODAS as correções do usuário → novo rascunho.
11. **Final** — `python3 ../../painel/gerar.py roteiro.json "previas/<Nome>_1080p.mp4"` (sem `--rascunho`),
    cópia leve de entrega (~350 MB, 3 Mbps), `gerar_srt.py`, capítulos com os tempos reais, créditos,
    capas (seção 8). Arquivo grande: dividir com `split -b 340M` e mandar as partes + o comando para juntar
    (`copy /b a+b+c saida.mp4` no Windows, `cat a b c > saida.mp4` no Mac/Linux) + o tamanho em bytes.
12. **Shorts** — 3 cortes de ≤ 35 s ligados ao longo (`montar_shorts.py` do ep09), capas próprias, `SHORTS.md`.

---

## 5. O motor — o que o `roteiro.json` sabe fazer

Gerado pelo `montar_roteiro.py` (nunca à mão). Campos principais:
- Raiz: `modo: "cenas"`, `formato: "16:9"`, `tema`, `avatar`, `voz_arquivo`, `transcrever_pedacos: 75`,
  `apertar_pausas: false` (REGRA: nunca encurtar pausas), `cena_minima: 3.0`, `vigia_padrao: false` (narrador só
  nas cenas marcadas), `grao`, `mix` (ganho da música, fundo/efeitos sob a voz, limite de pico),
  `legendas.destaques` (palavras em dourado), `musica` (trilha), `titulo_ep` (título no meio da tela:
  `{"antes_da_batida": 5, "linhas": [...], "vermelho": "…", "centro": true}`), `cta` (tela final inscreva-se).
- Por batida (fala): `cena` ou `cenas` (várias, trocando em `"em": "palavra"`), `pausa_antes_s`, `ambiente`,
  `sons` (`em`, `atraso`, `volume_db`, `ate`, `saida`, `pan`, `tom`, `arquivo`), `musica`
  (`{"som": "nenhum"}` silencia; `"continuar": true` retoma do ponto certo), `sem_legenda`.
- Cenas: `imagem` + `zoom [a,b]` + `foco [[x,y],[x,y]]`; `video` (+`video_inicio`, `congelar: true` = não
  desacelerar); câmera 3D (`c3(...)` no montar); `vigia: true` (cenário do narrador); `tipo: "texto"` (ficha de
  máquina de escrever, com tempo de leitura automático); `tipo: "chat"` (tela de grupo de mensagens com texto,
  áudio, foto, vídeo; horário; "digitando"); `kanji` (texto na tela em luz/sangue); `efeitos: {"cctv": {cam,
  hora, data, queda}}` (câmera de segurança com relógio correndo e "SEM SINAL"); `atmos` (neblina, poeira).
- Transições (`entrada`): `fundir`, `corte`, `obturador`, `queimar`, `rasgo`, `hanji`, `nanquim`, `vela`…
- Novos (16/11): `look` (cor de cinema por episódio: `{"preset": "isan"|"noite_fria"|"vela"|"arquivo", "forca", "halacao"}`),
  `alinhamento_forcado: true` (palavras encaixadas no texto do roteiro — usar sempre), câmera 3D em camadas (padrão),
  `ferramentas/interpolar.py` (câmera lenta RIFE). Detalhes e medições em `video/PESQUISA_MOTOR.md`.
- Ritmo automático (`ritmo()` no montar): frase curta continua a imagem anterior, cena mínima, fusão que termina
  antes da voz. `PROTEGE = {…}` = falas que sempre trocam de cena (sustos, silêncios).
- Novos efeitos do tema: criar `pagina/<tema>.js` registrando em `KR.cenas` / `KR.efeitos` / `KR.trans`
  (ver `tailandia.js`) e incluir no `pagina/index.html`.

---

## 6. Voz e áudio (detalhes que custaram caro aprender)

- **Narração**: Gemini TTS (`gemini-3.8-flash-tts` ou o mais novo disponível) pelo `narrar_fluxo.py`
  (streaming; o pedido normal com texto longo dá 502). Voz fixa do narrador (no canal antigo: **Algenib**).
  Escolher a voz do canal novo por amostras (Charon, Orus, Iapetus, Algenib, Puck, Kore, Aoede, Leda…).
- Texto em blocos (5 por episódio), cada bloco com as **3 últimas frases do anterior** na frente; o Whisper acha
  onde o texto novo começa e corta o contexto (senão o timbre muda entre blocos). Números: o Whisper escreve
  "2021" para "dois mil e vinte e um" — o corte precisa aceitar algarismo.
- **O TTS lê a instrução de estilo em voz alta** se ela vier junto do texto. Formato que funciona:
  `"<instrução>. Diga: <fala>"` e cortar pelo Whisper na palavra seguinte a "diga" (`gerar_vozes.py → cortar()`).
  Nunca usar "a última ocorrência" do começo da fala (falas que repetem o começo quebram).
- Escrita estrangeira (hangul, tailandês, kanji) **nunca vai para o TTS**: só na tela. Corrigir pronúncia com
  `PRON` (troca por grafia fonética só no texto do TTS).
- Personagens: 1 chamada por fala INTEIRA (fala emendada soa errada); filtro do lugar (celular:
  `highpass 300 / lowpass 3600 / compressor`); nunca acelerar a fala; se a fala nova é mais curta, o bloco fecha
  0,6 s depois dela (sem buraco); se é mais longa, a pausa seguinte encolhe.
- **Pausas**: o motor insere `pausa_antes_s` no silêncio REAL entre frases (corrigido para preferir a pausa longa —
  antes cortava a 1ª palavra da frase seguinte depois de fala de personagem).
- Trilha: composta em numpy (sem direitos), −30 dB no roteiro + ganho do mix; silêncio antes dos sustos; música
  própria nos cartões; nunca ruído/chiado de fundo constante (o usuário odeia).
- Efeitos: biblioteca `painel/sons/`; Sonniss (archive.org) para sons reais; o usuário vetou um "som de mastigar"
  — sempre ouvir a amostra antes.
- ElevenLabs: créditos acabam; só para efeitos/música curtos e reaproveitáveis. Narração nunca.
- Mix final: −14 LUFS, pico ≤ −1 dBTP (o `gerar.py` já faz); conferir os "aviso salto" do revisar.

---

## 7. Imagem e vídeo

- Imagens e clipes de IA: o usuário gera (Flow/Gemini/etc.) a partir dos seus prompts. Prompts terminam com
  restrições: sem rostos visíveis (de costas, sombra, cabelo cobrindo), sem texto, sem marca d'água, estilo
  coerente (ex.: "shot on a smartphone, handheld, digital noise" para fotos de celular; "CCTV night vision" etc.).
- Escolha da variação: montar folha de contato (`montage`) e olhar TODAS antes de usar.
- Clipes: anotar trecho seguro; cortar antes de qualquer falha da IA (rosto, objeto que surge do nada).
- Câmera 3D (`camera3d.py`) em ~1/4 das imagens; Ken Burns leve (2–8%) nas outras; zoom grande só se o assunto
  inteiro couber. Nada de foco redondo artificial.
- Material real (fotos, arquivo, trailers) dá PESO de documentário: sempre com crédito na tela e na descrição.
- Mesma imagem no máximo 2–3 vezes; o narrador só nas seções dele, entrando e saindo junto com a fusão.

---

## 8. Publicação, capas e métricas

- **Título**: curto, pergunta ou promessa ("Por que o terror tailandês nunca deixa você em paz?").
- **Descrição** (limite 5.000 caracteres): gancho em 2 linhas, resumo, pergunta, **capítulos com os tempos
  reais** (calcular do `<video>.tempos.json`; capítulo de cartão começa ~7,8 s antes da 1ª fala), fontes,
  transparência sobre IA, créditos de filmes e de CADA foto CC (autor + licença + link curto
  `commons.wikimedia.org/?curid=ID`), chamada para inscrição, 3 hashtags. Tags ≤ 500 caracteres.
  Comentário fixado com a pergunta do fecho.
- **Capas (1280×720, < 2 MB)**: o estilo que o usuário aprovou no Ep10 — **imagem de câmera de segurança em
  visão noturna** (verde, pretos esmagados, linhas de varredura, aberração cromática, letreiro "CAM 01 · REC ·
  hora"), a figura pequena e assustadora no quadro, **texto enorme de 2 linhas** (Anton; branco + vermelho com
  brilho, contorno preto, levemente inclinado), bandeira/selo no alto à direita, **sem círculo e sem seta**,
  canto inferior direito livre (duração). Frases que funcionaram: "ELA ESTÁ LÁ DENTRO", "NÃO OLHE PRO CANTO",
  "NÃO ABRA A PORTA". Script de referência: `episodios/ep10-tailandia/publicacao/gerar_capas_v2.py`.
  Fazer 4–6 opções, o usuário escolhe 3 para o "Testar e comparar" do YouTube.
- Legenda `.srt` sempre (`gerar_srt.py`). Shorts: título curto, ligação com o longo.
- Métricas (vidIQ/Analytics, se conectados): CTR e retenção dos primeiros 30 s guiam o próximo episódio.

---

## 9. Checklist antes de mandar QUALQUER vídeo (erros reais que já aconteceram)

**Vídeo**
- [ ] Folha de contato (1 quadro a cada 6–8 s) do vídeo inteiro olhada; e 10–30 quadros/s nos pontos de troca.
- [ ] Varredura automática de "piscadas" (quadro diferente dos dois vizinhos) — só podem sobrar as intencionais
      (flash do obturador). Script de 15 linhas: diferença média de quadros em cinza a 15 fps.
- [ ] Narrador: não pode aparecer pequeno no canto ao sair de cena, nem dois narradores sobrepostos (falas
      seguidas do narrador = UMA cena só), nem legenda pulando de lugar. (Bugs corrigidos no motor em 16/11.)
- [ ] Título do episódio inteiro na tela (centralizado, letra diminui até caber).
- [ ] Nenhum vídeo/cartão desacelerado ("desacelerado para 0.86×" no log = erro): dividir a cena ou `congelar`.
- [ ] Trecho de filme sem plano solto de 1 s, sem letreiro/legenda gravada, sem logo; crédito em cima.
- [ ] Fichas/textos com tempo de leitura (aviso "fica inteiro só X s" = alongar a pausa seguinte).
- [ ] Rostos de IA: nenhum (cortar o clipe antes).

**Áudio**
- [ ] Transcrever com Whisper os 5–10 s em volta de cada fala de personagem: a narração seguinte começa inteira
      ("Mas Mateus…", não "Mateus…"), a legenda bate com o áudio (±0,4 s), sem buraco de silêncio > 1,5 s.
- [ ] Legenda de fala entre aspas não gruda na narração seguinte (corrigido no `blocos_legenda`).
- [ ] Toda mensagem/fala importante da história existe EM ÁUDIO quando o enredo depende dela (o usuário reclamou
      de uma mensagem só escrita que "não entrava" — virou áudio do personagem + texto na tela no tempo do áudio).
- [ ] Mensagens de chat: o `apos` conta do começo da TELA, não da fala.
- [ ] `revisar.py`: 0 erros; poucos "aviso mix"; "aviso salto" conferido de ouvido.

**Entrega**
- [ ] Commit + push dos scripts (sem mídia); vídeo mandado ao usuário com resumo claro do que mudou.

---

## 10. Adaptar ao tema novo (checklist do canal secundário)

1. Preencher a seção 0 com o usuário (nome, nicho, narrador, regras).
2. Criar `video/<canal>/` com `QUALIDADE.md`, `CONTINUAR.md` e `ESTUDO_CANAIS_<NICHO>.md` (estudar 5–10 canais do
   nicho: títulos, capas, duração, ganchos, frequência). Os episódios vão em `video/episodios/<sigla>-epNN-nome/`.
3. Tema visual: `painel/temas/<canal>.json` (cores, fontes); cenário do narrador (`painel/cenarios/`);
   avatar novo se houver narrador ilustrado (`preparar_avatar.py` a partir das poses PNG que o usuário gerar:
   conversa `c_*`, ênfase `e_*`, sombrio `s_*`). Sem narrador visível: `vigia_padrao: false` e nenhuma cena
   `vigia`.
4. Voz do narrador: amostras no Gemini TTS → escolha → fixar no `narrar.py`.
5. Marca recorrente do canal (equivalente ao "câmera de segurança"/"pano Pha Yant"): propor 3, prévia, aprovar.
6. Trilha-base do canal (script `sintetizar_<canal>.py`) e vinheta de inscrição própria
   (`painel/sons/vinheta_<canal>.wav` + `F.VINHETA` no `falas.py`) e CTA (`cta` no montar).
7. Episódio piloto curto (6–8 min) para calibrar tudo antes do formato longo.
8. Nada do canal antigo (nome "Último Abrigo", "O Vigia", avatar, vinheta) aparece no canal novo.

---

## 11. Referências rápidas de comandos

```bash
# folha de contato de imagens
montage $(for a in *.jpg; do echo -label "${a%.jpg}" $a; done) -tile 4x -geometry 360x203+3+3 folha.jpg
# quadros de um vídeo (1 a cada 8 s)
ffmpeg -i video.mp4 -vf "fps=1/8,scale=320:-2,tile=8x7" folha%d.jpg
# rascunho completo do episódio
cd video/episodios/<sigla>-epNN-x && ./rascunho.sh
# refazer só a mixagem reaproveitando a imagem (economiza 30 min)
python3 ../../painel/gerar.py roteiro.json previas/x.mp4 --rascunho --so-audio=previas/video_mudo.mp4
# render final + legenda
python3 ../../painel/gerar.py roteiro.json "previas/Nome_1080p.mp4"
python3 ../../painel/ferramentas/gerar_srt.py "previas/Nome_1080p.mp4.tempos.json" publicacao/legendas_pt-BR.srt
# dividir para enviar
split -b 340M -d -a 1 "previas/Nome_1080p.mp4" partes/Nome.mp4.parte
```

> Ao terminar cada etapa importante, registre em `video/<canal>/CONTINUAR.md` o estado atual e o próximo passo —
> assim qualquer sessão nova continua de onde parou.
