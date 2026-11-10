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
- **08/11/2026 — APROVADO pelo usuário (padrão da série):** narrador de meio corpo
  (`vigia_meio`), conversa automática nas pausas + ênfases marcadas, abertura com relâmpago, modo
  `cenas`. Referência: `episodios/ep01-o-retrovisor/roteiro.json`.
- **08/11/2026 — chamada para ação (fim de todo episódio):** canal do YouTube **Último Abrigo**.
  Após a última imagem (~1,3 s), tela final de 3,6 s: cena escurece, "Gostou dessa história?",
  botão vermelho INSCREVER-SE com sino, cursor clica (vira INSCRITO, sino balança, clique), nome do
  canal em dourado, Vigia apontando para o espectador. Campo `cta` do roteiro.
- **08/11/2026 — REGRA de troca de pose:** nunca trocar no meio de uma palavra. A troca cai no
  silêncio entre palavras, logo antes do trecho que a pose vai "falar". Conversa troca em fim de
  frase (sempre), em vírgula/reticências com pausa real, ou em pausa longa no meio da frase; a pose
  é escolhida pelo conteúdo do trecho quando possível. Ênfase entra logo antes da palavra-chave; a
  conversa não troca se uma ênfase vai entrar em até ~1 s; uma frase nova encerra a ênfase anterior.
  Evitar duas ênfases a menos de ~1 s uma da outra. Conferir no `.tempos.json` (lista de poses).
- **08/11/2026 — abertura:** cartão de abertura com a arte do episódio (série + "EP. NN" + título),
  ~2,4 s, relâmpago e trovão grave, aproximação lenta, corte seco para a 1ª cena junto com a 1ª
  frase da narração (campo `abertura`). O Vigia e as legendas só entram depois dela.
- **08/11/2026 — SOM (feedback do Ep. 02):** NADA de chiado/ruído de fundo (o usuário comparou a
  rádio/TV fora do ar — eram os ambientes de casa, geladeira e chuva). Usar **trilha instrumental de
  verdade, baixa e tensa** (`trilha_tensa_1` contida, `trilha_tensa_2` crescente, geradas no
  ElevenLabs Music) e **SILÊNCIO** nos momentos-chave: antes/sob as frases de revelação e no clímax.
  Estática só dentro da gravação da câmera de segurança (aprovado). Efeitos pontuais e limpos.
- **08/11/2026 — cenário do Vigia (a partir do Ep. 03):** o topo da torre de vigia, "o Último
  Abrigo" (`painel/cenarios/abrigo_16x9.png` e `abrigo_vertical.png` para Shorts): mesa com casos,
  mural com fotos e linha vermelha, luneta, lampião e velas, lua crescente na janela gótica.
  Vigia em destaque à esquerda (sobre a poltrona); legenda e chamada final à direita/embaixo.
- **09/11/2026 — LINGUAGEM DE SOM E EDIÇÃO (estudo + feedback do Ep. 02):**
  - **Hierarquia fixa:** voz > efeito-chave > trilha > ambiente. Nada pode encobrir o narrador.
  - **Mixagem automática (`automixar` no motor):** enquanto o narrador fala, a trilha fica ~8 dB abaixo
    da voz e os efeitos ~3 dB abaixo; nos respiros (sem voz) trilha e efeitos sobem — é ali que a tensão
    aparece. Teto: nenhum efeito passa de +2 dB sobre a voz típica (corrige "trovão estourado"), trilha
    nunca passa de −3 dB. O motor imprime um relatório e avisa onde algo encobriu a voz.
  - **Sustos depois da palavra, não em cima:** o impacto (braam/stinger) cai no fim da palavra-chave
    (`"depois": true`), de preferência depois de 0,3–1 s de silêncio. Silêncio antes do susto, nunca
    música crescendo até ele sem pausa.
  - **Vocabulário de efeitos:** riser (subida de cordas) para preparar uma revelação; braam/sub-drop
    para a revelação; stinger de cordas para o susto rápido; respiração/passos baixinhos para presença;
    batimento para pânico contínuo. No máximo 1 efeito-chave a cada ~30 s — repetição mata o susto.
  - **Ambientes (chiado de casa, chuva, estática):** só dentro da cena que pede (ex.: gravação da câmera)
    e baixos; nunca amplificados junto com a trilha.
  - **Edição — onde cortar:** na mudança de ideia ou na pausa da voz; corte seco nas revelações; manter
    a imagem quando a frase é longa (movimento lento), trocar mais rápido na escalada.
  - **Vigia sozinho (aparte):** a cada ~2–3 min, o Vigia no cenário dele quebra a história com algo que
    enriquece: uma **curiosidade real** ligada ao tema, uma **pergunta direta** ao espectador ("você
    teria aberto?"), uma **pista** que o público deve guardar ("guarde esse detalhe") ou um **teste**
    ("não olha pra trás agora"). Curto (10–20 s), em silêncio ou com a trilha baixa, e volta para a
    história num corte seco. É também a quebra de padrão que segura a audiência.
- **09/11/2026 — Vigia em ALTA RESOLUÇÃO (`avatares/vigia_hd/`, 29 poses, rosto ~450 px):** padrão a
  partir do Ep. 03. Inclui 5 poses de **café** (caneca com a lua — ideia do usuário) para os apartes e
  a chamada final. Poses com fundo escuro/brilho são recortadas com `rembg` (modelo isnet-anime).
- **09/11/2026 — FORMATO "TEMA + HISTÓRIA" (pedido do usuário):** cada episódio longo une um tema real a
  uma história sinistra. Ordem: cold open (pico da história, ~15 s) → abertura → **tema** (psicologia, corpo,
  filosofia; no MÁXIMO ~90 s, só curiosidades que dá vontade de contar, terminando com algo para o público
  "guardar") → "Agora que você entende isso… vamos para a história de hoje." → história com 2–3
  **inserções no estilo Fyori** (fato real em cartão emoldurado ou tela preta, ligado ao que acabou de
  acontecer) → epílogo que **fecha o que o tema deixou guardado**. Edição mista: no tema os TIPOS de imagem
  se alternam a cada 3–6 s; na história, tela cheia e mais lenta. Modelo: `episodios/ep04-medo-do-escuro/ROTEIRO.md`.
- **09/11/2026 — VIGIA SÓ NAS INSERÇÕES (relato de espectador: ele tirava a concentração e a tensão):** na
  história o Vigia NÃO aparece. Ele aparece só no tema da abertura, nas inserções Fyori, nos apartes e no
  epílogo/CTA. No roteiro: `"vigia_padrao": false` e `"com_vigia": true` nas cenas das inserções (ou
  `"sem_vigia": true` cena a cena). Ele entra e sai sempre no corte da imagem.
- **09/11/2026 — luz em volta do Vigia:** o halo antigo era cortado num retângulo (aparecia "quadrado") e o
  contorno verde forte o deixava com cara de adesivo. Agora: elipse suave sem bordas, fraca, cor neutra
  (`halo_suave` no tema), recorte de luz bem sutil, sem brilho extra. Ele tem que se misturar com a cena.
- **09/11/2026 — SOM SEM SUSTOS BARULHENTOS:** o objetivo é tensão e medo, não pulo de volume. Padrão
  `sem_sustos` na mixagem: trilha nunca passa de 6 dB abaixo da voz típica e efeitos de 3 dB abaixo, mesmo
  nos silêncios; todo efeito entra com subida de 0,25 s. O motor avisa "salto" se trilha+efeitos subirem
  mais de 9 dB de repente. Tensão = drone crescente, riser, respiração, silêncio, passos — não braam alto.
- **09/11/2026 — duração dos episódios longos: 13 a 15 minutos** como referência. **10/11: passar de 15 min
  não é problema** — nunca cortar pausas, silêncios ou saídas lentas para caber no tempo. O que manda é o
  episódio ser bem produzido.
- **09/11/2026 — vídeos curtos reais:** `buscar_imagens.py videos` / `baixar_videos` (Pixabay, sem crédito
  obrigatório) — já tratados com a cor "documento" da série. **O motor toca vídeo na cena:**
  `"cena": {"video": "videos/x.mp4", "video_inicio": 2.0, "velocidade": 0.8, "zoom": [1.0, 1.04]}` (zoom, foco,
  transições e `sem_vigia` funcionam igual às imagens). Clipe mais curto que a cena é desacelerado até 0,6× e
  depois congela no último quadro — nunca repete (loop denuncia edição barata). Quadros ficam em cache em
  `painel/.cache_quadros/` (pode apagar; ~4 MB por segundo de vídeo). Custo medido: ~6% a mais de renderização.
  Uso: 1 vídeo a cada 3–5 imagens, de preferência em clima/ambiente (chuva, vela, corredor, olho), não em
  revelações (a revelação é corte seco para imagem parada).
- **09/11/2026 — NADA DE "CARA DE IA" EM PERSONAGEM (uma das ideias centrais do usuário):** o vídeo tem que
  parecer produção elaborada, não IA. Personagem pode aparecer, mas nunca com rosto inteiro e nítido: de costas,
  silhueta, sombra, cortado pelo quadro, desfocado, pelo vão da porta / olho mágico / vidro, ou só as mãos. A foto
  tem cara de "tirada por alguém" (celular à noite, flash, tremida, foco errado), nunca luz de cinema ou pose.
  O tratamento **"arquivo"** (`buscar_imagens.py arquivo`: cópia de cópia, alto contraste, ruído, riscos) é
  o recurso para imagem que AINDA tenha rosto com cara de IA. Imagem bem enquadrada (silhueta, olho mágico,
  mão, vidro) entra como está — testado no Ep. 04: o "arquivo" estourava as imagens escuras do usuário. Testado: só escurecer NÃO resolve; o
  enquadramento é o que mais pesa. Para close de olho/rosto, preferir vídeo real (Pixabay). Modelo de prompts:
  `episodios/ep04-medo-do-escuro/PEDIDO_IMAGENS_IA.md`.
- **10/11/2026 — SAÍDA DE CENA TENSA É LENTA (feedback do Ep. 04):** entrar na tensão pode ser corte seco;
  SAIR nunca. Depois de um momento pesado, a imagem fica na tela em silêncio (1–3 s) e só então passa devagar
  (fundir/preto de 1,2–2,2 s) para a próxima, com a transição acontecendo DENTRO do silêncio
  (`saida_lenta()` no montar_roteiro: `pausa_antes_s` + `entrada` + `antecipar`). No clímax, não cortar para
  outra imagem (ex.: close de olho) — fica na criatura. Sempre analisar cada corte: se a cena é de tensão,
  a troca não pode tirar a tensão que o espectador está sentindo. Abertura logo após o cold open: `"segurar"`.
- **10/11/2026 — texto digitado maior:** telas "máquina" (frases longas) agora têm letra de 7% da altura do
  vídeo (76 px em 1080p; antes 56 px). Telas curtas de impacto continuam no estilo próprio.
- **10/11/2026 — efeitos no silêncio:** no máximo 8 dB abaixo da voz típica (`efeitos_pico_max` −8). Com −3,
  os sub_drops depois de "Ela sorriu." etc. ainda soavam como pancada. Narração longa: `narrar_fluxo.py`
  (streaming) funcionou — 11min46 de áudio em 110 s, uma chamada só.
- **10/11/2026 — MÚSICA DE FUNDO CONTÍNUA (regra central do usuário):** uma música sinistra toca o episódio
  INTEIRO, baixa mas audível — é ela que dá o clima; narração e efeitos são o complemento. No roteiro:
  `"ambiente_inicial": [{"som": "<trilha longa>", "volume_db": -9}]` (passa pela mixagem automática: abaixa sob
  a voz, sobe nas pausas) e `"ambiente": {"som": "nenhum"}` na batida da vinheta final. A trilha é composta em
  código no comprimento do episódio (`ferramentas/sintetizar_trilha.py saida.mp3 800`), sem loop. Por cima, só
  reforços ATONAIS (drones) nos trechos de tensão — nunca uma 2ª música tonal (embola).
  **"Silêncio" = silêncio de NARRAÇÃO. Nunca silêncio total** (parece que o áudio cortou). Se a música parar,
  tem que ser um momento pensado para criar tensão, que não pareça erro.
  Trilhas recusadas: `suspense_forte` (soava como ruído), `suspense_atencao` (fraca). Toda trilha nova: medir a
  "ruidez" (planura espectral); as boas ficam abaixo de ~0,04.
- **10/11/2026 — tempo de leitura:** toda tela de texto fica INTEIRA na tela pelo menos 1,5 s + 0,3 s por palavra
  (o motor imprime "aviso leitura"; corrigir com pausa de narração antes da fala seguinte). "20 MINUTOS" sumia.
- **10/11/2026 — sincronismo:** o Whisper marca o início de frases depois de pausa cedo demais (até 1 s); o motor
  agora encosta esses inícios no fim do silêncio real (`ajustar_inicios`). Antes de enviar qualquer versão:
  conferir fala x legenda em vários trechos (alvo 0,0–0,3 s).
- **10/11/2026 — chiado da narração:** o Gemini entrega a voz com ruído de fundo em ~−49 dB, que aparece nas
  pausas. Sempre limpar antes de montar: `ffmpeg -i voz.wav -af "afftdn=nr=18:nf=-50:tn=1,highpass=f=70" voz_limpa.wav`
  (−8 dB de chiado, voz intacta).
- **10/11/2026 — pausas inseridas nunca no meio da palavra:** o motor põe a pausa no silêncio real logo antes
  da próxima palavra (o Whisper às vezes erra o fim da palavra: "olhar." foi cortado ao meio no Ep. 04 = glitch).
  Conferir depois de renderizar: nenhuma pausa com som acima de −40 dB colado nela.
- **10/11/2026 — imagem-chave escura demais:** se a criatura não aparece no celular, criar versão `_clara`
  (sombras levantadas + luz suave tipo luar sobre a figura, cantos escuros) e mirar os closes na cabeça real.
- **10/11/2026 — VINHETA FINAL (fim de todo episódio longo):** a tela de inscrição não pode ficar muda.
  Fala fixa do Vigia (`painel/sons/vinheta_cta_voz.wav`, Gemini/Algenib): "Se você ficou até aqui… então já é
  um dos meus. Inscreva-se no Último Abrigo e ative o sininho, pra não perder o próximo caso. Eu vou estar
  aqui. Esperando." + música-assinatura `vinheta_ultimo_abrigo` (caixinha de música, cello, sino distante).
  Como usar: emendar a fala no fim da narração (1,8 s de pausa), última batida com `"cta_inicio": true` e o
  texto da vinheta, `cta.clique_em: "Inscreva-se"` (o botão é clicado nessa palavra) — ver Ep. 04.
- **10/11/2026 — MÉTRICAS DO EP. 03 (primeiras 24 h) e o que muda a partir do Ep. 05:**
  ~1.600 impressões (o tema/título é entregue), mas **CTR de 1,06%** (baixo) e **duração média de 1min54 em
  11min53** (~16%: o público sai logo no começo).
  - **Capa:** alto contraste, UMA figura ou detalhe escondido que incomode na hora (a forma no canto, um olho
    no escuro, a silhueta na porta), sem poluição: no máximo 2–3 palavras grandes, ou nenhuma. Sempre gerar
    2–3 versões para o "Testar e comparar" do YouTube Studio.
  - **Título:** curto e direto, gancho misterioso ou ordem/ameaça (≤ 5 palavras antes do "| Creepypasta");
    deve criar uma pergunta que só o vídeo responde. Capa e título contam coisas DIFERENTES (não repetir).
  - **Gancho (0–45 s):** começar DENTRO da cena mais tensa da história — imagem forte nos primeiros 2 s, a
    pergunta/ameaça dita nos primeiros 5–8 s — e só depois a abertura e o contexto. Nada de contextualização
    lenta antes de prender. O cold open passa de ~15 s para **30–45 s**, com um "laço aberto" ("até o fim
    você vai entender por que…").
  - **Tema (formato tema + história):** depois do gancho, no máximo ~60 s e entremeado de imagens fortes; ou
    dividido em pílulas ao longo da história em vez de um bloco no começo.
  - Conferir no YouTube Studio → Retenção do público onde está a queda (0:30? 1:00? na abertura?) e anotar aqui
    a cada episódio, para saber se a mudança funcionou.
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

## 12. Decisões de 09/11/2026
- **Digitação:** som de teclado **mecânico (clicky)** — `painel/sons/teclado_mecanico_clicks.npy`, um clique
  sorteado por letra, ritmo humano; volume −26 dB (impacto −23) para nunca cobrir sussurros. Escolhido pelo
  usuário entre 5 opções.
- **Imagens: modelo híbrido aprovado.** Fotos reais de uso livre em ~60–70% das cenas (ambientes, objetos,
  clima, arquivo histórico) + IA só nos momentos-chave (criatura, susto, personagem).
  Ferramenta: `painel/ferramentas/buscar_imagens.py` (Pixabay com `PIXABAY_API_KEY` nas variáveis de ambiente,
  Openverse e Wikimedia sem chave). Gera folha de contato para escolher, baixa em alta, aplica o tratamento
  "documento" (dessatura, escurece, tom frio, vinheta) e grava `CREDITOS.txt` → copiar créditos CC BY/BY-SA
  na descrição do vídeo. Pexels: emissão de chaves pausada pelo próprio site (não usar).
- **Histórias:** fotos reais funcionam melhor quando **recontamos** casos/lendas/fatos; nas histórias originais
  do usuário, a IA continua, mas no **estilo foto documental** (abaixo).
- **Estilo das imagens de IA (novo padrão):** parecer foto real tirada por alguém e anexada a um dossiê/
  documentário — nada de "arte digital". Base de prompt:
  `amateur documentary photograph, shot on an old digital camera / 35mm film, natural available light, slight
  motion blur, flash falloff, film grain, muted cold colors, imperfect framing, everyday ordinary place,
  realistic textures, no cinematic lighting, no fantasy art, no CGI look` — referência: a foto do braço
  robótico de laboratório usada na amostra (luz fria, cores lavadas, enquadramento de registro).
- Amostra aprovada: 3min37 do Ep. 03 com fotos reais (roteiro gerado a partir de `ep03-conceito/roteiro.json`).
- **Títulos (regra do usuário):** todo título termina com **" | Creepypasta"** — no longo e nos Shorts
  (nos Shorts: `<título> | Creepypasta #shorts`). Palavra de busca forte do nicho; aumenta o alcance.

## 13. Auditoria do canal (vidIQ + Analytics, 10/11/2026) — o que adotamos
O usuário decidiu **manter o estilo** (O Vigia, tema + história, edição dinâmica); a auditoria entra como ajuste,
não como troca de formato. Números de partida: 165 inscritos, conversão 0,4% (Shorts dão views, não inscritos);
longos com 47–130 views e retenção 14–26%; tráfego 62% feed de Shorts, 33% busca, quase nada de "sugeridos".
Sinal positivo: o Short animado "O Vigia #01" fez 363 views em 2 dias (melhor início desde abril) → a série
numerada do Vigia é o diferencial do canal.
- **Constância acima de tudo:** meta de **1 longo por semana + 3–4 Shorts**, por 90 dias, antes de avaliar.
  A pausa de 7 meses (e perder o Halloween) custou mais que qualquer capa.
- **Shorts ≤ 35 s** (os de 1 min ou mais e os de 6–12 s foram mal). Frase-gancho e imagem forte no **primeiro
  0,5 s**, lugar concreto (corredor de hospital, casa na quaresma). Os nossos s2 (51 s) e s3 (61 s) do Ep. 03
  estavam longos demais — a partir de agora, cortar.
- **Todo Short é teaser de um longo:** termina em aberto e usa o recurso **"Vídeo relacionado"** do YouTube
  apontando para o episódio. Cada longo gera 3 Shorts de ≤ 35 s.
- **Títulos:** manter "| Creepypasta"; nos Shorts, frase limpa + no máximo 2 hashtags (nunca repetidas).
  Acrescentar uma promessa quando couber (um número, "o que a ciência explica", "nunca contei") — **sem
  chamar de REAL uma história que é ficção** (os fatos reais das inserções podem ser a promessa).
- **Tags:** só do nicho (terror, creepypasta, o tema do episódio). Limpar as tags erradas dos Shorts de março
  (Danganronpa, lareira, Baba Yaga, espanhol) e os títulos com "#terror #terror"/erros de digitação.
- **Formatos que estão fora da curva no terror BR** (testar sem largar o Vigia):
  1. **Compilação longa** (40 min+): "Os casos do Vigia — N histórias para ouvir no escuro", juntando episódios
     já prontos com pontes curtas do Vigia (custo baixo, nenhuma narração nova além das pontes).
  2. **Versão para dormir:** a mesma compilação com chuva contínua por baixo e sem efeitos de susto.
  3. **Folclore brasileiro como tema** do formato tema + história (lobisomem, Quaresma, Cruzeiro das Almas,
     causos do interior) — entra nos próximos episódios.
- **CTR:** meta acima de 5% nos longos (ver no Studio → Alcance). Retenção e CTR anotados aqui por episódio.
