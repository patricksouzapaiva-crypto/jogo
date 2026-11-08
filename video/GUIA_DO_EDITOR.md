# Guia do Editor — vídeos narrados com imagens paradas

Manual de trabalho do Claude como editor de vídeo do Mapa das Ideias. Junta o que foi estudado
(livros e práticas de montagem, documentários com fotos, vídeos curtos de retenção alta, projetos
abertos de edição feita por IA) com o que foi **testado de verdade** neste repositório.
Toda nova orientação sua entra na seção **11. Orientações da casa**, que vale mais do que
o resto do guia.

---

## 1. O fluxo de trabalho (sempre nesta ordem)

1. **Brief**: assunto, objetivo emocional, formato (9:16 Reels/TikTok/Shorts · 16:9 YouTube ·
   4:5 ou 1:1 feed), duração, voz (masculina/feminina, tom), restrições de fatos.
2. **Roteiro falado**: escrito *para o ouvido*. Frases curtas, uma ideia por frase, números por
   extenso quando forem ditos. Gancho nos 3 primeiros segundos. Cerca de 150 palavras por minuto.
3. **Decupagem (storyboard)**: o roteiro vira uma lista de cenas. Cada cena tem a frase que cobre,
   a imagem (prompt), o movimento de câmera, a transição de entrada e a duração estimada.
   **Mostrar ao usuário e esperar aprovação antes de gastar créditos.**
4. **Voz**: gerar a narração com marcação de tempo (seção 5). A partir daqui a **voz manda**: as
   durações das cenas se ajustam aos tempos reais das frases.
5. **Imagens**: gerar, revisar uma por uma (anatomia, mãos, texto acidental, marca d'água,
   coerência de personagem) e refazer o que falhar.
6. **Montagem**: escrever o `roteiro.json` e renderizar a **prévia** (`--rascunho`, em meia
   resolução).
7. **Autoavaliação**: extrair quadros em cada transição e conferir legendas, cortes, cor e áudio
   (checklist na seção 9). Corrigir e renderizar de novo, até 3 vezes, antes de mostrar.
8. **Entrega**: renderização final, loudness medido, arquivo enviado com legenda e capa sugerida.
9. **Memória**: registrar no projeto o que o usuário aprovou ou rejeitou, para virar regra da casa.

---

## 2. Princípios de montagem

**A regra dos seis, de Walter Murch** (*In the Blink of an Eye*). Um corte é bom, em ordem de
importância, se respeita:

1. a **emoção** do momento;
2. a **história**: faz a narrativa avançar;
3. o **ritmo**: entra no tempo certo;
4. o **olhar**: o olho do espectador encontra o ponto de interesse da nova imagem onde estava
   olhando na anterior;
5. o plano 2D da tela;
6. o espaço 3D.

Se a emoção estiver certa, o público perdoa quase todo o resto.

**Com imagens paradas, isso se traduz em:**
- **Edite pelo sentido da narração, não pelo relógio.** A imagem muda quando a *ideia* muda. O
  corte cai no início da palavra que introduz a ideia nova, ou numa pausa da voz.
- **Uma imagem = uma ideia.** Se a frase fala de duas coisas, são duas imagens.
- **O olhar conduz.** Se o ponto de interesse da cena A termina à direita, a cena B deve ter o seu
  ponto de interesse perto dali, ou o movimento deve levar o olho até ele.
- **O movimento tem motivo.** Aproximar = intimidade, tensão, revelação de um detalhe. Afastar =
  contexto, solidão, conclusão. Panorâmica = percorrer, comparar, seguir uma direção (tempo,
  viagem). Subir = esperança, grandeza. Descer = peso, queda.
- **Uma direção por sequência.** Não alternar esquerda/direita sem motivo: cansa o olho. Numa
  sequência de passagem de tempo, todas as panorâmicas vão para a mesma direção (da esquerda para
  a direita, o sentido de leitura, sugere "avançar").
- **Nada fica 100% parado.** Mesmo a cena "parada" respira com 1 a 2% de zoom. Uma imagem
  congelada por mais de 3 ou 4 segundos parece travamento.
- **Silêncio é ferramenta.** Meio segundo sem voz antes da revelação principal vale mais do que
  qualquer efeito.

---

## 3. Ritmo por formato

| Formato | Duração | Troca de imagem | Observações |
|---|---|---|---|
| Reels/TikTok/Shorts (9:16) | 30–75 s | a cada 2,5–4 s | gancho em 0–3 s; promessa em 3–5 s; nada de introdução |
| YouTube (16:9) narrado | 3–12 min | a cada 4–7 s | pode respirar mais; capítulos com mergulho no preto |
| Feed (4:5) | 20–45 s | a cada 3–5 s | precisa funcionar **sem som** (legenda obrigatória) |

- **Gancho:** a primeira imagem precisa ser a mais forte do vídeo e a primeira frase precisa ser
  uma pergunta concreta ou uma afirmação surpreendente (o padrão das capas do Mapa das Ideias).
  Nunca abrir com logo, "olá" ou contexto.
- **Quebras de padrão a cada 8–12 s:** mudar a escala (plano geral → detalhe), a direção do
  movimento, a paleta ou a presença de texto na tela. Isso reinicia a atenção.
- **Final:** a última frase fecha a promessa do gancho. Termina com a imagem mais "aberta" e um
  fade de 1 s. O CTA (se houver) é falado, único e curto, como no guia da marca.

---

## 4. Vocabulário de câmera e transições

### Movimentos (motor: campo `movimento`)

| Nome | Efeito | Quando usar |
|---|---|---|
| `aproximar` | zoom 1,00 → 1,12 | revelação, tensão, foco num rosto ou objeto |
| `afastar` | zoom 1,14 → 1,00 | contexto, conclusão, solidão |
| `esquerda` / `direita` | panorâmica horizontal | percorrer uma cena larga, passagem de tempo |
| `subir` / `descer` | panorâmica vertical | ótimo em 9:16 com imagem alta (prédio, árvore, pessoa inteira) |
| `parado` | respiração 1,04 → 1,05 | texto na tela, momento contemplativo |

- **Velocidade:** de 8% a 15% de zoom em 4–6 s. Mais do que isso parece "efeito de aplicativo".
  Sempre com curva suave (`senoide`); **nunca linear**.
- Personalizável por cena: `"zoom": [1.0, 1.2]`, `"centro": [[0.3,0.4],[0.5,0.5]]` (frações da
  imagem). Use `centro` para começar num detalhe (um olho, uma carta) e terminar no todo.

### Transições (motor: campo `transicao` = entrada da cena)

| Transição | Significado | Duração |
|---|---|---|
| `corte` | continuidade; o padrão dentro de uma mesma ideia | 0 |
| `fundir` (dissolve) | passagem de tempo, associação entre ideias | 0,6–1,2 s |
| `preto` (mergulho no preto) | fim de capítulo, mudança de época, antes da revelação | 0,6–1,0 s |
| `luz` (fusão com clarão quente) | memória, sonho, flashback | 0,8–1,2 s |

Regra: **o corte seco é o padrão**; cada transição "com efeito" precisa ter um significado.
Nunca usar cortinas, giros ou slides decorativos: denunciam amadorismo.

---

## 5. Voz (ElevenLabs — conectado)

- **Endpoint com tempos:** `POST /v1/text-to-speech/{voice_id}/with-timestamps`. Ele devolve o
  áudio em base64 e o `alignment` com `characters`, `character_start_times_seconds` e
  `character_end_times_seconds`. **Testado aqui:** funciona em português com
  `eleven_multilingual_v2` e `language_code: "pt"`. O motor transforma os caracteres em palavras
  para a legenda.
- **Modelos disponíveis:** `eleven_v4`, `eleven_v3` (mais expressivo, aceita marcações de emoção
  entre colchetes), `eleven_multilingual_v2` (o mais estável para narração longa), `flash`/`turbo`
  (rápidos e mais baratos, para rascunho).
- **Vozes testáveis para histórias:** George (britânico, "storyteller"), Daniel ("broadcaster"),
  Brian (grave). Todas são multilíngues no modelo v2/v3. Para soar nativo em PT-BR, vale buscar
  uma voz brasileira na biblioteca de vozes e fixar o `voice_id` nas orientações da casa.
- **Ajustes:** `stability` 0,4–0,55 (abaixo fica teatral, acima fica robótico),
  `similarity_boost` 0,75, `style` 0,15–0,3.
- **Gere por parágrafo**, não o texto inteiro de uma vez: refazer um trecho fica mais barato. Use
  `previous_text`/`next_text` para manter a entonação contínua entre os trechos.
- **Orçamento:** plano Starter, cerca de 9 mil caracteres restantes no ciclo atual (≈ 9 min de
  narração). Um Reel de 60 s gasta ≈ 900 caracteres.
- Pronúncia: escreva nomes estrangeiros como devem ser lidos na *voz* (o texto da legenda pode
  manter a grafia correta, editada à parte).

---

## 6. Imagens

### Direção de arte
- **Um mundo visual por vídeo**, escolhido do cardápio de estilos do `config.yaml` (óleo
  renascentista, aquarela, xilogravura, noir...). Repetir o mesmo sufixo de estilo em todos os
  prompts.
- **Prompts narrativos, não listas de palavras-chave:** quem, fazendo o quê, onde, que luz, que
  enquadramento. Termine com: "vertical composition, main subject in the middle third, no text,
  no letters, no watermark".
- **Gere com sobra:** a imagem precisa ser pelo menos 1,3–1,5× o quadro final para o zoom não
  borrar (o motor aumenta com Lanczos quando necessário, mas a nitidez real vem da fonte).
- **Varie a escala:** plano geral (contexto) → plano médio (ação) → detalhe (mãos, objeto,
  carta). A sequência de escalas é o que faz imagens paradas parecerem filmadas.
- **Personagem recorrente:** criar primeiro uma *folha de personagem* (rosto de frente, de
  perfil, corpo inteiro) e passá-la como imagem de referência em todos os prompts seguintes
  (modelos Gemini "Nano Banana" aceitam várias referências). Descrever no prompt o que pegar de
  cada referência.
- **Pessoas reais históricas:** retratar de forma respeitosa e verossímil; não inventar fatos
  visuais que contradigam o dossiê.

### Zonas seguras em 9:16 (1080×1920)
- Topo ~250 px e base ~420 px ficam cobertos pela interface do Instagram/TikTok.
- A legenda fica a ~22% da base (o motor já faz isso). Ponto de interesse da imagem no terço do
  meio.

### Provedores (situação testada em 07/11/2026)
| Provedor | Situação | Observação |
|---|---|---|
| Gemini (`gemini-3-pro-image`, `gemini-3.1-flash-image`, `gemini-2.5-flash-image`) | conectado, mas **cota 0 no plano gratuito** (erro 429) | precisa ativar faturamento no Google AI Studio; é o melhor para consistência de personagem (aceita `imageConfig.aspectRatio: "9:16"` e `imageSize: "2K"`) |
| Pollinations anônimo | funciona | só 576×1024 e **com marca d'água**: serve apenas para teste |
| Pollinations com `POLLINATIONS_TOKEN` | não configurado nesta sessão | resolução e modelo melhores, sem custo |

---

## 7. Música, efeitos e mixagem

- **Níveis:** voz sempre na frente. A música fica 15–20 dB abaixo da voz (`volume_musica_db`
  −18 a −22) e **abaixa sozinha quando a voz fala** (sidechain: compressor da música acionado pela
  voz, ataque de 40 ms, soltura de 600 ms). Nos respiros, ela sobe naturalmente.
- **Tratamento da voz:** filtro passa-alta em 80 Hz (tira ronco) e compressor suave 3:1.
- **Loudness final:** **−14 LUFS integrado, pico real ≤ −1 dBTP**, normalizado em **duas
  passadas** (`loudnorm` com `linear=true`; uma passada só deixa o som "bombeando"). **Testado:**
  o motor entrega −14,0 LUFS.
- **Música:** instrumental, sem letra, no clima do mundo visual (cordas e piano para drama
  histórico; ambiente para reflexão). Começa com fade de 1,5 s e termina com fade de 2,5 s.
  Use música com licença clara (biblioteca do usuário, trilha gerada por IA com direito de uso, ou
  a síntese do animation-studio).
- **Efeitos sonoros discretos** valorizam imagens paradas: papel, pena, lareira, trem, vento.
  Sempre baixos (−25 dB) e sincronizados com a entrada da imagem.
- Fades de 30 ms em todo corte de áudio para não estalar.

---

## 8. Legenda, cor e acabamento

- **Legenda:** 2 a 4 palavras por bloco; quebra em pontuação ou em pausa de 0,35 s; nenhum bloco
  dura menos de 0,35 s. Fonte sem serifa pesada (Inter/Montserrat), branco quente `#F7F3EB` com
  contorno escuro e **a palavra falada em coral `#E63946`** (a cor da marca). Legenda é sempre a
  **última camada**, por cima de tudo.
- **Texto de tela** (datas, nomes, títulos de capítulo): pouco, grande, com tempo de leitura de
  pelo menos 1,5 s mais 0,3 s por palavra.
- **Cor:** o mesmo tratamento em todas as cenas é o que transforma imagens diferentes num filme:
  contraste levemente maior, saturação ~0,9, temperatura puxada para o mundo visual (quente para
  óleo/vela, fria para noir), **vinheta** de 25–30% e **granulação** fina e animada (mais nas
  sombras).
- Granulação forte aumenta muito o tamanho do arquivo e é borrada pela recompressão das redes:
  manter entre 0,02 e 0,035.

### Especificação de entrega
- H.264 High, `yuv420p`, CRF 18, 30 fps, AAC 192 kbps 48 kHz, `+faststart`.
- 9:16 = 1080×1920 · 16:9 = 1920×1080 · 4:5 = 1080×1350 · 1:1 = 1080×1080.

---

## 9. Checklist de autoavaliação (antes de mostrar qualquer coisa)

- [ ] O gancho funciona **sem som** e nos primeiros 2 s?
- [ ] Cada troca de imagem cai numa mudança de ideia ou numa pausa (nunca no meio de uma palavra)?
- [ ] Algum movimento está rápido demais, tremido ou com borda aparecendo?
- [ ] Alguma imagem fica parada mais de 6 s sem quebra de padrão?
- [ ] As transições têm significado? (corte seco é o padrão)
- [ ] Imagens: mãos e rostos corretos, nenhum texto acidental, **nenhuma marca d'água**,
      personagem coerente entre as cenas?
- [ ] Legendas: sincronizadas, sem erro de grafia, dentro da zona segura, sem esconder o
      ponto de interesse?
- [ ] Áudio: voz inteligível com a música, −14 LUFS ±1, sem estalos nos cortes, final sem
      corte seco?
- [ ] Fatos batem com o dossiê? Datas e nomes escritos certos?
- [ ] O final responde à promessa do começo?

Para conferir os quadros: `ffmpeg -i video.mp4 -vf "select='eq(n,30)+eq(n,120)',scale=360:-1,tile=4x1" -frames:v 1 folha.png`.
Para medir o áudio: `ffmpeg -i video.mp4 -af ebur128=peak=true -f null -`.

---

## 10. O motor (`video/motor/editor.py`)

```bash
pip install opencv-python-headless numpy   # e ffmpeg com libass
python video/motor/editor.py roteiro.json saida.mp4 --rascunho   # prévia rápida, meia resolução
python video/motor/editor.py roteiro.json saida.mp4              # final
```

Por que um motor próprio em vez do `zoompan` do ffmpeg: o `zoompan` arredonda a posição para
pixels inteiros e **treme** nos zooms lentos (bug conhecido). O motor desenha cada quadro com
posição em subpixel (`warpAffine` + Lanczos), por isso o movimento fica liso.

Exemplo de `roteiro.json` (caminhos relativos ao próprio arquivo):

```json
{
  "formato": "9:16", "fps": 30,
  "voz": "voz.mp3", "alinhamento": "alinhamento.json", "inicio_voz": 0.6,
  "musica": "trilha.mp3", "volume_musica_db": -18,
  "legendas": true, "palavras_por_legenda": 3, "cor_destaque": "#E63946",
  "grade": {"contraste": 1.06, "saturacao": 0.92, "quente": 0.05, "vinheta": 0.3, "granulacao": 0.03},
  "cenas": [
    {"imagem": "01.png", "duracao": 3.8, "movimento": "aproximar"},
    {"imagem": "02.png", "duracao": 3.8, "movimento": "direita", "transicao": "fundir", "duracao_transicao": 0.9},
    {"imagem": "03.png", "duracao": 3.5, "movimento": "afastar", "transicao": "preto", "duracao_transicao": 0.8}
  ]
}
```

- `alinhamento` é o objeto `alignment` devolvido pelo ElevenLabs, salvo como JSON.
- A última cena se estica sozinha para cobrir o fim da voz.
- Desempenho medido (4 núcleos de CPU): ≈ 10 s de renderização por segundo de vídeo 1080×1920.
  Um Reel de 60 s leva cerca de 10 minutos; a prévia leva cerca de 1/4 disso.

### Próximos passos possíveis (ainda não feitos)
- **Paralaxe 2.5D:** mapa de profundidade (Depth Anything) para o fundo e o primeiro plano se
  moverem em velocidades diferentes. É o maior salto de "cara de cinema". O projeto aberto
  DepthFlow faz isso, mas precisa de GPU; dá para fazer uma versão leve em CPU dentro do motor.
- **Momentos com movimento real:** a ferramenta ManyMotions (conectada) transforma imagem em vídeo
  curto. Usar só em 1 ou 2 cenas-chave por vídeo (custo e estabilidade).
- **Texto de tela animado** (datas, nomes) e **efeitos sonoros** automáticos por cena.
- **Gerador de roteiro.json** a partir do roteiro + alinhamento: cortar cenas exatamente nas
  fronteiras de frase.

---

## 11. Orientações da casa

> Aqui entram as orientações do usuário, com data. Elas valem mais do que tudo acima.

- **07/11/2026 — estilo-alvo definido:** "avatar + painel animado" (motion graphics com título
  cinético, painel de interface que se constrói a cada frase e avatar em pixel art com poses),
  sincronizado palavra por palavra com a narração. Análise completa em
  [`referencias/estilo-avatar-painel.md`](referencias/estilo-avatar-painel.md). O motor de
  imagens paradas continua disponível para vídeos de história, mas não é o padrão.
- **07/11/2026 — vozes e sons:** narração **sempre pelo Google Gemini TTS** (grátis), nunca pelo
  ElevenLabs. O ElevenLabs fica só para **trilha de fundo e efeitos sonoros essenciais**, gerados
  curtos, uma vez, e guardados em `video/painel/sons/` para reaproveitar.
- **07/11/2026 — personagem:** O Vigia (31 poses em `video/painel/avatares/vigia/`), canal de
  terror. Motor do estilo em [`painel/`](painel/README.md).
- **07/11/2026 — série O VIGIA (terror), linguagem definitiva em teste no ep. 01 "O Retrovisor":**
  imagens estáticas cinematográficas em tela cheia (modo `cenas` do motor), 1080×1920, 30 fps,
  50–55 s; zooms de 2–5%; **cortes secos** nas revelações; nada de transições chamativas.
  O Vigia fica no canto inferior esquerdo (18–25% da largura), sem animar a boca; atua por troca de
  pose junto das mudanças de imagem. Legenda: sans-serif, branco quente, sombra discreta, máx. 2
  linhas, poucas palavras-chave destacadas. Som: chuva/vento/motor abafado contínuos, drone grave
  minimalista, efeitos pontuais. Última imagem ~1 s após a narração.
- **Regra de ouro da série:** em sequências de aparição (ex.: retrovisor vazio → silhueta → rosto),
  **cortes secos** com **mudança simultânea de som e de expressão do Vigia** — é isso que faz o
  público sentir a entidade se mover. Nunca suavizar essas transições.
- **08/11/2026 — Vigia com presença (feedback do ep. 01):** ele estava apagado e trocava pouco.
  Agora: ~26% da largura, brilho e contraste realçados, luz de contorno fria, halo atrás, leve
  movimento no ritmo da própria voz (envelope da narração) e **troca de pose a cada ~2 s** em
  palavras com sentido (não só a cada imagem), com um pequeno impulso de escala na troca.
- **08/11/2026 — narrador novo (corpo inteiro, `avatares/vigia_corpo/`):** a **prancha 1 (16 poses)
  é a CONVERSA**: o motor troca sozinho entre elas a cada ~1,5–2 s, no início de palavras/frases,
  sem repetir as últimas — pequenas diferenças que dão vida. A **prancha 2 (12 poses) é a ÊNFASE**:
  só nas palavras-chave (campo `enfase` da batida), segura ~1,5–2 s com impulso maior e a conversa
  volta. No roteiro marca-se apenas a ênfase.
- **08/11/2026 — narrador definitivo em teste: meio corpo (`avatares/vigia_meio/`, 48 poses):**
  prancha A = conversa automática (prefixo `c_`), B = ênfase exagerada (`e_`), C = tom sombrio
  (`s_`, conversa nas batidas com `"tom": "sombrio"` e ênfases frias). Rosto 2,5–3× maior que o
  de corpo inteiro → bem mais nítido no celular. Cabeça sempre na mesma posição; base dissolvida.
- **08/11/2026 — abertura:** cartão de abertura com a arte do episódio (série + "EP. NN" + título),
  ~2,4 s, relâmpago e trovão grave, aproximação lenta, corte seco para a 1ª cena junto com a 1ª
  frase da narração (campo `abertura`). O Vigia e as legendas só entram depois dela.
- **Regras permanentes da série:** terror psicológico; gancho forte nos primeiros segundos;
  terminar com revelação ou imagem inquietante; não explicar demais o sobrenatural; estrutura
  simples e reutilizável; nunca substituir o Vigia.
- **Voz (Gemini, cota grátis = 10 narrações/dia por modelo, compartilhada com os vídeos do Caio):**
  narrar o episódio inteiro numa chamada só. `gemini-3.8-flash-tts` lê qualquer direção em voz
  alta → mandar só o texto (`so_texto`), voz Algenib; `gemini-3.1-flash-tts-preview` aceita
  direção mas bloqueou o texto longo de terror por "SAFETY"; o 2.5 aceita direção simples.

---

### Fontes estudadas
- Walter Murch, *In the Blink of an Eye* — a regra dos seis ([StudioBinder](https://www.studiobinder.com/blog/walter-murch-rule-of-six/), [No Film School](https://nofilmschool.com/2016/11/6-rules-good-cutting-according-oscar-winning-editor-walter-murch)).
- Ken Burns e o uso de fotos em documentário ([NEH](https://www.neh.gov/humanities/2015/septemberoctober/feature/the-civil-war-ken-burns-reinvented-the-television-history-d), [MasterClass](https://www.masterclass.com/articles/how-to-use-the-ken-burns-effect-in-a-documentary)).
- browser-use/video-use — edição feita por agente de IA: regras de produção, legendas, loudness, autoavaliação em cada corte ([GitHub](https://github.com/browser-use/video-use)).
- Tremido do `zoompan` e soluções ([Bannerbear](https://www.bannerbear.com/blog/how-to-do-a-ken-burns-style-effect-with-ffmpeg), [patch FFmpeg](https://lists.ffmpeg.org/pipermail/ffmpeg-devel/2020-February/257073.html)).
- DepthFlow — paralaxe 2.5D a partir de uma imagem ([GitHub](https://github.com/BrokenSource/DepthFlow)).
- ElevenLabs — fala com marcação de tempo ([documentação](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps)).
- Consistência de personagem com Gemini ([Google Codelab](https://codelabs.developers.google.com/gemini-consistent-imagery-notebook), [Runway](https://help.runwayml.com/hc/en-us/articles/50317213804435-Creating-images-with-Nano-Banana)).
- Loudness em redes e normalização em duas passadas ([DEV — loudnorm](https://dev.to/masonwritescode/two-pass-loudness-normalization-with-ffmpeg-loudnorm-the-right-way-1nm3), [OpenClip](https://openclip.app/learn/loudness-standard)).
- Ganchos e ritmo em vídeos curtos ([CapCut](https://www.capcut.com/create/short-form-video-hooks-first-3-second-patterns), [Metricool](https://metricool.com/viral-video-hooks/)) — números de "retenção" desses sites são de marketing, usados só como direção.
