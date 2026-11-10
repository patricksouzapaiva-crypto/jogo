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

- **Ep. 05 "Abre, filha." — Cabra Cabriola (10/11):** pasta `episodios/ep05-cabra-cabriola/` (o Papa-Figo ficou em `ideias/`).
  ROTEIRO.md escrito (aguarda aprovação antes de narrar), PEDIDO_IMAGENS_IA.md (14 prompts), PEDIDO_MUSICA_SUNO.md,
  busca de fotos/vídeos em `busca/`. Fora do episódio por decisão do usuário: bacurau (Freyre) e voz clonada por IA.

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
