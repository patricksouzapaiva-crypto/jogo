# Referência: estilo "avatar + painel animado" (enviado em 07/11/2026)

Vídeo de referência: anúncio patrocinado de 24,6 s, em 9:16 (gravado da tela do Instagram, 576×1280).
Este é o estilo-alvo do novo sistema. **Não é** o estilo de imagens paradas com movimento de
câmera (`video/motor/editor.py`): aqui tudo é *motion graphics* desenhado em código e sincronizado
com a narração palavra por palavra.

## Anatomia da tela (de cima para baixo)

1. **Fundo**: marrom-escuro quente com brilho radial suave no centro; **perfurações de filme**
   nas laterais; **cantoneiras** finas (como visor de câmera) nos cantos; pequenos **"+"
   cintilando** em posições aleatórias; assinatura pequena no canto superior direito
   (`usuario / avatar`).
2. **Título cinético** (canto superior esquerdo, ~2 linhas): fonte condensada e pesada, toda em
   maiúsculas (estilo Bebas/Anton). **Linha 1 em branco; linha 2 dentro de uma caixa dourada com
   texto escuro.** O título é *digitado letra a letra* no ritmo da fala e resume a frase dita
   ("SEM CÂMERA", "SEM LUZ", "SEM VERGONHA", "NÃO É DE / 10 SEGUNDOS"). Ele faz o papel da
   legenda: **não há legenda corrida**.
3. **Painel central** (cartão de interface): moldura dourada fina, com uma **etiqueta pequena** no
   topo ("PRECISA DE QUÊ?", "DURAÇÃO", "CORTES", "ANTES EU ACHAVA", "CHAT", "SEU AVATAR"). O painel
   **persiste por várias frases e vai se construindo**:
   - **lista que se risca**: cada item entra digitado, com ícone; um traço vermelho risca o ícone
     ("sem câmera / sem luz / sem vergonha");
   - **comparação de duração**: "videozinho 0:10" riscado → "vídeo longo" com contador subindo
     (00:10 → 03:49 → 11:12) e a grade de miniaturas crescendo;
   - **corte**: a faixa horizontal de miniaturas é cortada (tesoura) e vira 3 quadros verticais com
     selos REELS / TIKTOK / SHORTS;
   - **checklist em papel creme**: "Pra ter canal precisava:" + itens com caixinha, ícone e barra;
   - **chat**: balão do usuário digitado ("Faz um vídeo sobre a Suíça"), três pontinhos de
     "digitando", e a resposta como arquivo `suica_final.mp4` com barra de progresso;
   - **tela preta de impacto**: campo de estrelas + frase pequena digitada + frase grande
     sublinhada ("ISSO MUDA O JOGO.");
   - **grade final** de miniaturas ("MONTE O SEU AVATAR") = chamada para ação.
4. **Avatar** (base, centro): personagem em pixel art dentro de um **halo dourado**, troca de
   **pose a cada ideia** (apontando, pensando, joinha/OK, mãos no rosto, braços abertos) com um
   leve balanço contínuo.
5. **Barra de XP** no canto inferior direito (detalhe de "jogo" da identidade).

## Ritmo e som

- Narração de voz sintética, rápida: **≈ 3,3 palavras/s**. Uma ideia a cada 2–4 s; o título
  troca a cada frase e o painel troca a cada 2–3 frases (continuidade).
- Praticamente **sem música**: nos respiros o áudio cai para ≈ −36 dB. Só a voz e, no máximo,
  efeitos discretos (cliques de digitação, "pop" dos itens). Voz bem alta e limpa.
- Tudo entra com animação curta (100–250 ms): digitar, crescer com leve "pulo", riscar,
  encher barra. **Nada é corte seco de tela inteira**; a tela é sempre a mesma e só o conteúdo
  muda.

## Estrutura do roteiro (fórmula do anúncio)

| Tempo | Função | Fala |
|---|---|---|
| 0–3,5 s | gancho por eliminação de dores | "Sem câmera, sem luz, sem ficar com vergonha de aparecer." |
| 3,5–7,9 s | quebra de objeção | "E não é um videozinho de 10 segundos. Dá pra fazer vídeo longo…" |
| 7,9–13,4 s | bônus | "E desse longo ainda saem os cortes verticais pro Reels, pro TikTok, pro Shorts." |
| 13,4–17,9 s | antes (crença antiga) | "Antes eu achava que pra ter canal tinha que aparecer, ter voz bonita, saber editar." |
| 17,9–20,2 s | depois (solução) | "Hoje eu só peço e ele entrega." |
| 20,2–22,9 s | público + frase de efeito | "Pra quem tem vergonha de câmera, isso muda o jogo." |
| 22,9 s– | CTA | "Quer montar o seu avatar e fazer vídeos…" |

## Como reproduzir (plano técnico)

- Desenhar em **HTML/Canvas** e renderizar quadro a quadro em Chromium headless (já instalado),
  ou no motor do animation-studio; tudo vetorial, nítido em 1080×1920.
- **A narração manda**: a voz é gerada com marcação de tempo (ElevenLabs `with-timestamps`) e
  cada animação é ancorada a uma palavra ("risca o ícone quando disser *câmera*").
- Roteiro em JSON por *batidas*: `{fala, titulo: [linha1, linha2], painel: {tipo, itens...},
  pose_avatar}`; uma biblioteca de painéis reutilizáveis (lista riscada, checklist, contador,
  chat, upload, grade de miniaturas, tela de impacto, corte em verticais).
- Avatar: um conjunto de PNGs de poses (pixel art) do personagem da casa.
