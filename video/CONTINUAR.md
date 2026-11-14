# Para continuar numa sessão nova

Leia antes de qualquer coisa: `video/GUIA_DO_EDITOR.md` (regras da casa, seções 11 e 12) e
`video/ESTUDO_CANAIS_TERROR.md`. O motor está em `video/painel/` (`gerar.py`, `pagina/motor.js`, `render.js`).

## Estado em 09/11/2026
- **Ep. 01 "O Retrovisor"** (Short) e **Ep. 02 "A Sonâmbula"** (longo + 3 Shorts): prontos e entregues.
- **Ep. 03 "Mais perto."** (11min52): **aprovado** (v4, teclado mecânico). Publicação em
  `episodios/ep03-conceito/publicacao/YOUTUBE.md` + `legendas_pt-BR.srt`.
  Renderizar de novo: `python3 video/painel/gerar.py video/episodios/ep03-conceito/roteiro.json saida.mp4`
  (a narração `audio/voz_completa_v2.wav` não vai pro git — se faltar, pedir ao usuário ou regravar).
- **Imagens reais:** modelo híbrido aprovado (seção 12 do guia). `PIXABAY_API_KEY` foi cadastrada nas
  variáveis de ambiente pelo usuário — testar logo no começo:
  `python3 video/painel/ferramentas/buscar_imagens.py buscar /tmp/t consultas.json`.

- **Shorts do Ep. 03 (09/11):** os 3 renderizados e enviados ao usuário (s1 26 s, s2 51 s, s3 61 s, −14 LUFS).
  Re-renderizar: `cd video/episodios/ep03-conceito && python3 montar_shorts.py` e depois
  `cd shorts && python3 ../../../painel/gerar.py s3_o_microfone.json saida.mp4`. Sem a narração completa,
  o `montar_shorts.py` reaproveita os recortes `shorts/*_voz.wav`.
- **Pixabay testado (09/11): funciona.** Mas a chave foi posta no *script de configuração* do ambiente
  (sem `export`), então NÃO chega à sessão: passar no comando ou pedir ao usuário que a mova para as
  variáveis de ambiente.
- Contêiner novo precisa de: `pip install faster-whisper opencv-python-headless numpy requests`.

- **Ep. 04 "Não acenda a luz." (tema + história, ~14 min): roteiro APROVADO** (`episodios/ep04-medo-do-escuro/ROTEIRO.md`).
  Prontos: 25 fotos reais tratadas (`imagens_reais/`) e 15 vídeos curtos (`videos/`), com créditos.
  13 imagens-chave do usuário em `imagens/` (aprovadas, sem tratamento extra). `montar_roteiro.py` → `roteiro.json`
  pronto (138 falas, 156 cenas, Vigia só nas inserções, trilha/efeitos/ênfases definidos).
  **PRONTO em 10/11** (narração em fluxo OK, render final 12min42, enviado em 720p). Histórico: a cota do `gemini-3.8-flash-tts` acabou em 09/11 (~22h UTC). A chamada normal com o
  texto inteiro dá 502 depois de ~30 s → usar `painel/ferramentas/narrar_fluxo.py narracao_texto.txt
  audio/voz_completa.wav` (streaming, ainda não testado até o fim). Se der erro, dividir em 4 blocos (seções).
  O usuário escolheu ESPERAR a cota para manter a mesma voz (Algenib) — não trocar de modelo.
- Motor (09/11): Vigia fora por padrão (`vigia_padrao`), halo corrigido, som `sem_sustos`, aviso de salto de volume.

- **Métricas do Ep. 03 (10/11):** CTR 1,06% e retenção média 1min54/11min53 → regras novas no guia
  (capa/título/gancho de 30–45 s). Valem do **Ep. 05** em diante; o Ep. 04 segue como está.

- **Ep. 04 PRONTO PARA POSTAR (10/11):** vídeo 1080p enviado ao usuário; `episodios/ep04-medo-do-escuro/publicacao/`
  tem 3 capas, YOUTUBE.md (3 títulos, descrição PT/ES/EN com capítulos e créditos, tags, comentário, config.) e
  legendas pt-BR/es/en (.srt; `painel/ferramentas/gerar_srt.py` + `traduzir_srt.py`, Gemini de texto com vários
  modelos de reserva — a cota grátis de cada um acaba rápido).
- **Música por IA do Google:** a conta tem `lyria-3.5` (gerador de música) na mesma API do Gemini — testar como
  alternativa ao ElevenLabs (sem créditos) para as trilhas de fundo dos próximos episódios.

- **Auditoria do canal (10/11):** resumo e decisões na seção 13 do guia. Estilo mantido; mudanças: constância
  (1 longo + 3–4 Shorts/semana), Shorts ≤ 35 s ligados ao longo, testar compilação de 40 min+ e folclore BR.

- **Shorts do Ep. 04 (10/11):** 3 prontos e enviados (33 s cada, −14,5 a −15,5 LUFS): `episodios/ep04-medo-do-escuro/
  montar_shorts.py` (aceita `pular` para cortar batidas e manter ≤ 35 s; pausas de leitura limitadas) e
  `publicacao/SHORTS.md` (títulos, descrições, ordem 3 → 1 → 2). Próximo passo: decidir o Ep. 05 com o usuário.

- **Ep. 05 "Abre, filha." — Cabra Cabriola (10/11):** pasta `episodios/ep05-cabra-cabriola/` (Papa-Figo e outras
  lendas ficaram em `ideias/`). Prontos: `ROTEIRO.md` (**aguarda aprovação do usuário antes de narrar**),
  `PEDIDO_IMAGENS_IA.md` (14 prompts B01–B14, enviados no chat; aguardando as imagens), `imagens_reais/` (~40 fotos
  tratadas) e `videos/` (25 clipes) com CREDITOS.txt. Fora do episódio por decisão do usuário: bacurau (Freyre) e
  voz clonada por IA.
  **Música (decidida):** trilha composta em código, aprovada pelo usuário (`sintetizar_piano_violino.py fundo2/tensao2`
  → `painel/sons/ep05_fundo_longa.mp3`, `ep05_tensao_longa.mp3`); cantiga do Suno entra sozinha (`ep05_cantiga.mp3`).
  Não usar músicas prontas "livres" (risco de Content ID) — ver fim do `PEDIDO_MUSICA_SUNO.md`.
  **Imagens:** as 14 imagens-chave do usuário estão em `imagens/` (B01–B14); +45 fotos sinistras em `imagens_reais/`.
  Próximos passos: aprovação do roteiro → narração (Gemini em fluxo, Algenib) → `montar_roteiro.py` → render.

## Pendências
0. Ep. 04: (a) ~~vídeo dentro da cena~~ FEITO; (b) narração Gemini (uma chamada); (c) montar roteiro.json
   com o Vigia só nas inserções; (d) renderizar e revisar.
1. Aguardando o usuário aprovar os 3 Shorts do Ep. 03.
3. Estudo de **edição de som** no estilo Fyori: o YouTube bloqueia download aqui ("confirme que não é um robô");
   usar as gravações que o usuário enviar. Ideia: separar voz/fundo (demucs) e medir onde entram efeitos,
   silêncios e trilha em relação às palavras.
4. Músicas via KIE.AI/Suno (`painel/ferramentas/musica_kie.py`) — aguardando conta/chave do usuário.

## Regras que o usuário cobra sempre
Narração pelo Google Gemini TTS (grátis); ElevenLabs só para música/efeitos e pouco. Troca de pose só entre
palavras. Nada de chiado. Trilha presente mas nunca por cima da voz; silêncio como ferramenta. Não encurtar
as pausas da narração. Vigia em alta resolução, troca de lado às vezes. CTA no fim. Nunca pedir chave no chat.


## Estado em 11/11 (madrugada) — Ep. 05 em render final
- Roteiro aprovado, narração pronta; falas-chave trocadas pela voz da mãe (Gacrux, aprovada pelo usuário: "A") e
  áudio da Marina (Leda): `trocar_vozes.py` → `audio/voz_personagens.wav` (não vai pro git; refazer com o script,
  precisa de `audio/voz_com_vinheta_limpa.wav` = narração do backup mp3 + vinheta, limpa com afftdn).
- Correção de cor: `gradar.py` → pasta `grade/` (não vai pro git; rodar de novo após clonar).
- Som novo (voz de estúdio, bolso, som de lugar) aprovado pelo usuário ("Gostei muito").
- Render: `python3 ../../painel/gerar.py roteiro.json previas/ep05_final.mp4` (~1 h). NÃO rodar ffmpeg pesado em
  paralelo com a codificação final: o contêiner reiniciou por falta de memória.
- Depois do vídeo aprovado: pacote de publicação (3 capas, títulos, descrição com créditos, legendas, Shorts).

## Ep. 05 ENTREGUE (11/11) — vídeo aprovado e pacote de publicação pronto
- Vídeo final corrigido enviado ao usuário (`previas/O_Vigia_Ep05_Abre_filha.mp4`, 13min18; não vai pro git).
- `publicacao/`: 3 capas, `YOUTUBE.md`, legenda pt-BR, 3 Shorts (≤35 s) com capas, .srt e `SHORTS.md`.
- Lição: a imagem B14 "sombra na escada" era a foto do Ep. 04 arquivada errada — CONFERIR cada imagem recebida
  olhando o arquivo antes de dar nome. Foi trocada por `escada_sinistra_2`/`escada_sinistra_0`.
- Próximos: coletar CTR/retenção do Ep. 05 após 48 h; Ep. 06 (releitura de creepypasta), Ep. 07 (medo: oceano).

## Ep. 06 em roteiro (11/11) — "Não deixa a gente dormir." (releitura do Experimento Russo do Sono)
- Tema escolhido pelo usuário. `episodios/ep06-experimento-do-sono/PESQUISA.md` e `ROTEIRO.md` (rascunho, aguardando
  aprovação). Sem sangue (o original é gráfico). Vozes de personagem só no interfone e na gravação final.
- PENDENTE no canal: as tags de "Ela não dormia" (vídeo dsfFvTHiLPY) foram postas como insônia/experimento do sono
  por engano — o vídeo é o Ep. 02 "A Sonâmbula" (sonambulismo). Corrigir quando o usuário autorizar (5 créditos).
  O título dele segue travado por teste "Testar e comparar". A capa nova da sereia (y2i10N0kpCo) foi recusada.

## Ep. 06 mudou (11/11): "Escadas na mata" — `episodios/ep06-a-porta-na-mata/ROTEIRO.md (v2: portas em vez de escadas, bombeiros, o Remedo — ideia do usuário)` (rascunho, aguardando aprovação)
- O experimento do sono foi descartado pelo usuário depois de 4 versões ("não está me agradando"); os rascunhos
  ficaram em `episodios/ideias/experimento-do-sono/`.
- O que o usuário quer numa releitura: NÃO pode parecer cópia; precisa de diferencial claro, versão brasileira,
  e EXPLICAR o que está acontecendo (não deixar em aberto como o original). Bem sinistro; descrever com palavras, sem imagem gráfica.

## Ep. 06 "A porta na mata" — ROTEIRO v3 APROVADO (11/11)
- `episodios/ep06-a-porta-na-mata/ROTEIRO.md` (190 falas, ~13 min) e `PEDIDO_IMAGENS_IA.md` (P01–P19 + clipes V01–V05).
- Usuário assinou Google AI Pro (app Gemini, Flow, Nano Banana Pro). A CHAVE DA API continua no nível gratuito:
  imagem e música dão 429 (testado 11/11). Para eu gerar sozinho, ele precisa ativar faturamento no projeto da
  chave no Google AI Studio. Enquanto isso: ele gera as imagens/clipes no app e me manda.
- Próximos passos: receber imagens → conferir fatos (Shackleton, Innocence Project) → buscar fotos/vídeos reais →
  compor trilha nova → narração (Vigia + voz do Caio) → montar_roteiro.py → rascunho → final → pacote.

## Ep. 06 em produção (11/11 noite) — rascunho em render
- Recebido do usuário e CONFERIDO imagem por imagem: 40 imagens (P01–P19 A/B, P08 C/D = versões antigas) em
  `imagens/` e 5 clipes do Flow em `clipes/` (V01 aproxima porta, V02 porta abre sozinha, V03 mata, V04 fogueira,
  V05 trilha/capacete — este tem perfil de rosto à direita: `gradar.py` corta).
- Fatos conferidos (Shackleton: South Georgia Museum/James Caird Society; Innocence Project: 69% de 375). Ajuste:
  "os três CONTARAM a mesma coisa" (Crean não escreveu).
- Narração: `narrar_fluxo.py narracao_texto.txt audio/voz_completa.wav` (646 s) + vinheta → `voz_com_vinheta_limpa.wav`;
  `alinhar.py` → `audio/alinhamento.json`. Voz do Caio (falas 45 e 51): `trocar_vozes.py [Puck|Achird|Orus]`
  DECISÃO DO USUÁRIO (12/11): a voz do Caio ficou "muito artificial, desconexa" → REMOVIDA; o Vigia narra as falas dele.
  Lição: voz de personagem só funciona com som de lugar (porta, telefone, rádio); voz seca ao ar livre soa falsa.
- Trilha nova em código: `painel/ferramentas/sintetizar_trilha_ep06.py` → `sons/ep06_fundo_longa.mp3`, `ep06_tensao_longa.mp3`.
  O usuário está gerando trilha no Flow Music (mandei 2 prompts: fundo e tensão); quando chegar, montar comparação.
- Sons de lugar/efeitos (ElevenLabs): `sons/ep06_*` (mata dia/muda/noite, riacho, rua, estalo, risada, riso da menina,
  porta, motor, vento do capacete). OS CRÉDITOS MENSAIS DO ELEVENLABS ACABARAM nesta leva (renovam no ciclo do plano).
- Canais de som: "ambiente" = som do lugar; "trilhas" = música (fundo ↔ tensão, nunca silêncio).
- Fotos reais: 23 fotos em `imagens_reais/` + 6 vídeos reais em `videos/` (Pixabay, Wikimedia, Flickr), com `CREDITOS.txt`.
  A CHAVE DO PIXABAY EXISTE: está no script de configuração do ambiente (sem `export`), então não chega à sessão.
  Para usar: ler com get_environment e passar no comando (`PIXABAY_API_KEY=... python3 buscar_imagens.py ...`);
  nunca gravar a chave no repositório. Pedido ao usuário: mover para as variáveis de ambiente.
- `montar_roteiro.py` garante sozinho o tempo de leitura das telas de texto (aumenta a pausa seguinte).
- Render: `python3 gradar.py && python3 trocar_vozes.py && python3 montar_roteiro.py && python3 ../../painel/gerar.py roteiro.json previas/ep06_rascunho.mp4 --rascunho`
  NÃO rodar gradar.py com render em andamento (reescreve os clipes de grade/).

## Vigia falando (lip-sync) — testado em 12/11/2026: funcionou (traço mantido, boca sincronizada); custo 379 créditos por clipe de ~8 s; vídeo sai em https://manymotions.com + caminho do result.video
- Ferramenta: conector **ManyMotions**, modelo `fal-ai/kling-video/ai-avatar/v2/standard`
  (`media_forge_generate`, type video, params `{image_url, audio_url, prompt}`); arquivos sobem com
  `video_editor_request_upload` + PUT. Exige plano ativo na conta conectada (deu `billing_required` antes).
- Teste: imagem = `cenarios/abrigo_16x9.png` + pose `vigia_hd/c_falando.png` centralizada (altura 660 em 1280x720);
  áudio = `ep03-conceito/audio/voz_completa_v2.wav` de 30,5 s a 38,7 s ("Boa noite. Bem-vindo de volta ao Último
  Abrigo. Me responde uma coisa, com sinceridade."), mono, mp3.
  Prompt: "The cartoon narrator speaks calmly and mysteriously to the camera, lip-synced to the audio, subtle hand
  gestures, blinking, keep the exact art style and background, static camera."
- Regra combinada: Vigia falando só nos **apartes em tela cheia**; no canto seguem as trocas de pose (grátis).
  Avisar quantos clipes antes de gerar (gasta créditos).
- API do Google (chave grátis): vídeo (Gemini Omni) e imagem (Nano Banana) têm limite 0 — só TTS funciona.
- Plano B grátis: boca animada pela voz (poses com boca fechada/aberta trocadas pelo volume da narração).

## 12/11 — Ep. 06 v3 (batidas reais) e Shorts refeitos
- Ep. 06 refeito com batidas reais do ElevenLabs (`ep06_batidas_v2`, `_fracas_v2`), `efeitos_pico_max` -3, pausas de
  isolamento (1,6 s antes da batida 40; 1,4 s antes da 44). Rangido da porta baixado para -15 (a -11 subia 2 dB acima
  da voz). Final: `previas/ep06_final_v3.mp4` → entrega `previas/O_Vigia_Ep06_A_porta_na_mata.mp4`. Tempos +3 s depois de
  2:55: legendas e capítulos do YOUTUBE.md já regerados.
- Shorts do Ep. 05 (1 e 2) e do Ep. 06 (1 e 2) refeitos; capas com texto na zona segura (y < ~1450) e sem repetir o título.
- **Disco:** cada render final deixa ~5 GB em `/tmp/painel_*` se falhar. Antes de um render longo, `df -h /`; apague as
  pastas antigas uma a uma (`rm -r /tmp/painel_XXXX`). Um render morreu em 12/11 por "No space left on device".
- Ep. 07: sons aprovados — corrente 5 (`ep07_corrente_base` + derivados longe/chegando/para/vai/rapida), respiração da
  criatura (`Rcriatura_a` → `ep07_respiracao_porta`/`_nuca`), gritos longe/perto. Falta: imagens do usuário.
- Teste 2 (CTA, 12/11): trecho "Inscreva-se no Último Abrigo e ative o sininho, pra não perder o próximo caso."
  (`sons/vinheta_cta_voz.wav` de 4,25 s a 9,6 s), pose `c_falando` à esquerda (x=30%, altura 640) para sobrar
  espaço ao botão; prompt pedindo olhos abertos na câmera e gestos com as duas mãos → bem mais natural.
  Custo ≈ 47 créditos por segundo de áudio (253 por 5,4 s). A fala inteira (12,9 s) custaria ~610, mas é
  gerada UMA vez e reutilizada em todos os episódios (a vinheta é fixa).

## 12/11 — Ep. 08 "A estação que não existe" (terror japonês + Kisaragi) — trailer APROVADO
- Pasta `episodios/ep08-estacao/`: ROTEIRO.md (documentário 1666→2004 + história da Dani; final novo do usuário:
  vigília no quintal e a Dani de branco na janela de cima → zoom → corte seco pro Vigia), PESQUISA.md (fontes),
  PEDIDO_IMAGENS_IA.md, `imagens_reais/` (gravuras e fotos reais limpas + CREDITOS.txt), `imagens/` (25 do usuário
  ampliadas, ORIGEM.txt), `trailer/` (montar_trailer.py, roteiro.json), `previas/O_Vigia_Ep08_trailer_v3.mp4` = aprovado.
- **Motor novo** (pagina/motor.js, 12/11): `cena.kanji` (5 modos: luz/sangue/tinta/recorte/placa; pincelada de fundo,
  hanko `selo`, respingos, `glitch`, `legenda`, `em`), transições `entrada`: nanquim/shoji/vela, `dof`, `mao`,
  paralaxe nas gravuras, `atmos` (neblina/poeira/vela/pelicula/fumaca), `celular {vertical, sinal}`, `zoom_digital`,
  tipos `chat` (família com nomes/cores/avatares), `mapa` (GPS com `some_em`), `capitulo` (第一章), `relogios`, e
  sobreposição `linha` (linha do tempo). Fontes japonesas: Yuji Syuku (pincel) e Shippori Mincho.
- **Som dos kanjis = `ep08_kanji`** (onda grave suave). O pincel áspero foi REPROVADO ("som de chocalho").
- Trilha `ep08_cx_tensao` (caixinha em escala in + koto + rin) — gerar a versão longa com
  `ferramentas/sintetizar_caixinha_ep08.py tensao ../sons/ep08_cx_tensao.mp3 1300`.
- Falta: imagens da noite da Dani (D01–D11), Hamamatsu/fábrica, J02–J09, clipes Flow; decisões do usuário: voz da
  Dani (2 áudios) e da mãe na vigília, título (recomendado "Ela desceu numa estação que não existe").

## 12/11 (noite) — Ep. 08 rascunho 2 APROVADO ("excelente") → render final 1080p
- Título aprovado: **"Por que o terror japonês é o mais pesado do mundo"**. Capa: "NÃO TEM REZA QUE DESFAZ." ou
  "VOCÊ SÓ PRECISA OLHAR." (não repetir o título). Vozes: Dani = Aoede, mãe = Gacrux (`trocar_vozes.py`).
- Trilha aprovada: `sons/ep08_japones_longa.mp3` (koto + shakuhachi, `ferramentas/sintetizar_japones_ep08.py`).
- Fluxo: `falas.py` → `narrar.py` (3 blocos; bloco 2 refeito com introdução pra não mudar o timbre) → `alinhar.py`
  → `trocar_vozes.py` → `montar_roteiro.py` → `painel/gerar.py roteiro.json previas/ep08_final.mp4`.
- **Regras de ritmo novas do usuário (valem para TODOS os episódios):** nada de troca de cena no meio da frase
  (uma cena por frase), sem cortes rápidos, legenda nunca muda de lugar, kanji/legendas pequenas com tempo de leitura,
  foco do `dof` no ponto certo, nenhum ruído tipo "TV fora do ar", música um pouco mais alta.
  `montar_roteiro.py: ritmo()` aplica mínimos (imagem 3,6 s; kanji c/ legenda 6,5 s; `linha` 6,5 s).
- Motor (12/11): `dof`/`zoom_digital` x,y agora em FRAÇÃO DA IMAGEM (`c._tf`); neblina sem emenda (fim da
  "linha passando"); legenda do kanji horizontal e maior; `linha` do tempo com faixa e destaque; chat sem sobrepor
  o cabeçalho, áudio com onda abaixo do nome; `mapa.progresso`; `inserir_silencios` com fades de 15 ms.
- Entrega: `previas/O_Vigia_Ep08_Por_que_o_terror_japones.mp4` + `publicacao/legendas_pt-BR.srt`.
- Pendente: pacote de publicação (capa, descrição com capítulos, Shorts) — pedir "pode" antes de mexer no canal.

## 13/11 — Ep. 08 corrigido: "Onze e quarenta, em Londrina" (era "meio-dia e quarenta"; Brasília–Japão = 12 h)
- `corrigir_hora.py` emenda a voz (mesma duração); `VOZ_TEMPOS=audio/voz_personagens_meiodia.wav` no gerar.py mantém os
  tempos aprovados; `render.js --quadros 0:298` redesenhou só o começo; emenda no keyframe de 9,933 s.
- **Vídeo final para subir no YouTube: `episodios/ep08-estacao/previas/O_Vigia_Ep08_Por_que_o_terror_japones_1080p.mp4`
  (1,5 GB, 37615 quadros).** Legenda: `publicacao/legendas_pt-BR.srt`. O usuário escolheu subir o de 1,5 GB (não fazer a
  cópia de 530 MB). Entrega pendente: o arquivo não cabe no chat (limite 400 MB) e esta sessão não pode criar Releases no
  GitHub (repo é PÚBLICO). Usuário escolheu "esperar" — opções: 4 partes de ~375 MB pelo chat + comando para juntar.
- `previas/ep08_final.mp4` e `ep08_final_v2_som.mp4` têm a legenda antiga (não usar).

## 13/11 — Ep. 08 ENTREGUE (o usuário posta)
- Vídeo 1,5 GB entregue em 4 partes (juntou com sucesso). `publicacao/`: YOUTUBE.md (título, capas E/A/F, descrição com
  20 capítulos, créditos, tags, comentário fixado), SHORTS.md + `shorts_final/` (3 Shorts, ordem 1 → 3 → 2), capas.

## 14/11 — Ep. 09 v3 "O que voltou da montanha" — EM PRODUÇÃO (a v2 "O quarto do andar F" foi PAUSADA: "lamento, não terror")
- Roteiro aprovado: ep09-coreia/ROTEIRO.md (175 falas; Rafa/Lívia; Jangsan-beom + Irmã Raposa + Jogo do Elevador + Gonjiam; 3 sustos).
- Vozes: Rafa Umbriel, Lívia Despina, pai Orus, mãe Sulafat (vozes/gerar_vozes.py). Narração: blocos 1, 2, 4 prontos; 3 e 5
  esperam a cota do Gemini (retomada agendada 14/11 08:20 UTC faz narração → vozes → alinhar → montar → rascunho.sh).
- Imagens: imagens_v3/ (76, conferidas; carimbos de data refeitos por carimbos.py numa linha do tempo só: subida 21/10,
  volta 24/10 06:15, cozinha 27/10 03:12, fotos do bicho 2013). Clipes Flow: clipes_v3/ (fora do git; notas em CLIPES_V3.md).
- Trailers: cortar_filmes.py → mimic_menina, gonjiam_lanterna, gonjiam_mato (+ mimic_mulher reserva), com crédito.
- Trilha: aprovadas 01–10 + novas 11_a_montanha, 12_jangsan (compressor nas batidas), 13_os_tenis. **ElevenLabs sem créditos até
  12/12**: o resto vem da biblioteca (painel/sons). Montagem: montar_roteiro.py (v3; o da v2 está em montar_roteiro_v2_bia.py).
- Qualidade: QUALIDADE.md + painel/ferramentas/revisar.py (rascunho.sh não renderiza se o roteiro tiver erro).

## 13/11 — Ep. 09 "O terror coreano é pior do que você imagina" (história: "O quarto do andar F") — EM PRODUÇÃO
- `episodios/ep09-coreia/`: ROTEIRO.md v2 APROVADO; vozes Bia = Leda, mãe = Sulafat, voz falsa no corredor = Sulafat
  sussurrada (`vozes/`). Imagens/clipes do Flow em `imagens/` e `clipes/` (B04 refeita: `regras_folha.py`).
- Fluxo: `falas.py` → `narrar.py` (4 blocos, Algenib) → `alinhar.py` → `trocar_vozes.py` → `montar_roteiro.py` →
  `rascunho.sh` (gera câmera 3D + `gerar.py --rascunho`). "B. A." (비아 lido errado) foi silenciado em
  `audio/voz_com_vinheta_limpa.wav` (original em `_original.wav`); o 비아 aparece pintado nesse silêncio.
- **Trilha nova, APROVADA ("ficaram excelentes")**: 10 faixas compostas por parte (ElevenLabs Music,
  `trilha/gerar_trilha.py`; instrumentos coreanos + tema de gayageum), checadas contra "pancada" (`trilha/analisar.py`),
  `montar_trilha.py` iguala volume e instala `painel/sons/ep09_m*.mp3`. Música mais presente: -7 dB sob a voz.
  **Pedido do usuário: no terror a música é o que mais marca — manter esse padrão (faixa por parte) nos próximos.**
- Motor novo: `ferramentas/camera3d.py` (Depth Anything V2: paralaxe real + foco de lente; cenas `c3(...)` no montar),
  `cortar_filmes.py` (Exhuma/Two Sisters: recorte sem logo Netflix, câmera lenta minterpolate, moldura "TRECHO DE FILME"
  com crédito, sem áudio; brutos e prontos fora do git), fontes coreanas Nanum (reserva das japonesas), chat `check`.
- Pedido do usuário (13/11): "atenção à iluminação, jogo de câmera e foco" — foco de cada imagem conferido na grade.
- Falta: rascunho para o usuário; depois final, capa ("NÃO RESPONDA DEPOIS DAS 3."), descrição, Shorts.
