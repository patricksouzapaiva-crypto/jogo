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
  (padrão Puck; amostras em `previas/amostras/` — o usuário ainda NÃO escolheu).
- Trilha nova em código: `painel/ferramentas/sintetizar_trilha_ep06.py` → `sons/ep06_fundo_longa.mp3`, `ep06_tensao_longa.mp3`.
  O usuário está gerando trilha no Flow Music (mandei 2 prompts: fundo e tensão); quando chegar, montar comparação.
- Sons de lugar/efeitos (ElevenLabs): `sons/ep06_*` (mata dia/muda/noite, riacho, rua, estalo, risada, riso da menina,
  porta, motor, vento do capacete). OS CRÉDITOS MENSAIS DO ELEVENLABS ACABARAM nesta leva (renovam no ciclo do plano).
- Canais de som: "ambiente" = som do lugar; "trilhas" = música (fundo ↔ tensão, nunca silêncio).
- Fotos reais: sem chave do Pixabay nesta sessão e Openverse instável → só 22 fotos (Wikimedia/Flickr) em
  `imagens_reais/` com `CREDITOS.txt`; 5 reaproveitadas dos Eps. 04/05.
- `montar_roteiro.py` garante sozinho o tempo de leitura das telas de texto (aumenta a pausa seguinte).
- Render: `python3 gradar.py && python3 trocar_vozes.py && python3 montar_roteiro.py && python3 ../../painel/gerar.py roteiro.json previas/ep06_rascunho.mp4 --rascunho`
  NÃO rodar gradar.py com render em andamento (reescreve os clipes de grade/).
