# Fauna preparada v2: relatório de preparação e teste

Origem: `MOVIMENTACOES_DOS_ANIMAIS_v1.zip` (as folhas de caminhada são idênticas às do `CAMINHADA_DOS_ANIMAIS.zip`; os hashes do manifesto conferem).
Espécies: Penala, pato anfíbio, ovelha, Gruntho e vaca. Ao todo, 340 poses: 5 × 32 de caminhada e 5 × 36 de ações.

**Situação:** os quadros estão preparados e **a caminhada foi melhorada (v2)**. A cena de teste roda no Godot 4.5 (117 de 117 verificações automáticas passaram, estáveis em 3 rodadas). **A integração com o sistema de animais do jogo ainda não foi feita**, porque este trabalho foi feito fora do projeto. Isso fica para o chat principal (veja `PROMPT_CHAT_PRINCIPAL.md`). Há 3 defeitos que ainda exigem redesenho e algumas decisões pendentes (abaixo).


---

## v2: o que melhorou no andar

A v1 continua em `revisao/v1/` para comparação, e o visualizador tem um botão v1/v2. As animações em `JogoFazenda/arte/preparado/fauna/` agora são da **v2**. Nada foi redesenhado e nenhuma parte do corpo foi recortada nem girada.

| Melhoria | Antes (v1) | Depois (v2) |
|---|---|---|
| **Sobe e desce do corpo** | Em 16 dos 20 ciclos o topo da cabeça ficava parado, o que dava cara de andar duro, "deslizando" | O corpo sobe 1 px na passagem, 2 vezes por ciclo (uma por passo), em ritmo regular. A fase segue os pés. A linha do quadril é duplicada (a perna "estica" 1 px) e os pés continuam no chão. A vaca e o pato de costas já tinham sobe e desce desenhado e foram mantidos. |
| **Pausas no ciclo** | Quadros quase repetidos ficavam o mesmo tempo que os outros. Exemplo: Penala para baixo, 0,20 s preso por ciclo | Quadros quase repetidos duram metade, e o tempo sobra para os outros (o ciclo continua com a mesma duração). Penala para baixo: 0,11 s. Ovelha para cima: de 0,29 s para 0,16 s |
| **Cintilação da textura** | De 38% a 66% dos pixels do corpo mudavam de tom à toa entre quadros | Penala de 11% a 17%, Gruntho de 25% a 35%, ovelha de 24% a 41%, pato de 29% a 46%. A vaca melhorou pouco (de 43% a 49%, porque o corpo dela se move mais entre quadros). Contorno, cabeça e cauda que mexem de verdade não são tocados. |
| **Gruntho de costas** | Só a pata traseira direita levantava | A esquerda também levanta, nos quadros 3 e 7 (correção provisória: a pata direita levantada foi espelhada para a esquerda sobre os quadros com as patas no chão; o corpo e a luz são os originais) |
| **Parar e voltar a andar** | Parado para baixo, para cima ou para a esquerda segurava o quadro 0 (às vezes no meio do passo) | Cada direção tem uma **pose de parado** (patas juntas, dois pés no chão, sem a subida do passo). Ao voltar a andar, a animação começa no quadro seguinte. |
| **Encaixe andar → ação** | Até 2 px de "pulo" quando o animal parava e virava para uma ação | As ações foram deslocadas para casar a silhueta com a caminhada para a direita (no máximo 1 px de diferença) |

Comparação animada: `revisao/comparacao_v1_v2/andar_v1_v2_lado.gif` e `andar_v1_v2_frente.gif`.

No JSON de cada caminhada: `duracoes` (por quadro), `parado` (quadro da pose de parado), `melhorias_v2` (o que mudou) e `ordem_sugerida_automatica` (só informativo; não aplicado).

---

## 1. O que foi feito, por etapa da missão

| Etapa | Situação |
|---|---|
| 1. Inspecionar o projeto | ⏳ **Pendente.** O projeto não estava acessível aqui. Nada foi alterado nele. |
| 2. Preparar os quadros | ✅ Recorte, alpha real, escala, canvas e pivot por espécie |
| 3. Organização real | ✅ Ordem das linhas lida do JSON (a ovelha tem direita e esquerda trocadas na folha) |
| 4. Continuidade | ✅ Medidas objetivas + inspeção visual. Defeitos registrados (seção 5) |
| 5. Movimento natural | ✅ Tempos por espécie e por ação (sugestões para testar). ⚠ ver seção 4 |
| 6. Transições | ✅ Testadas na cena de teste (automático): parado ↔ andar, troca de direção, ação → parado, ação interrompida |
| 7. Cena de teste | ✅ `JogoFazenda/testes/fauna/` (isolada; apague a pasta para remover) + visualizador web |

## 2. Como os quadros foram preparados

**Fundo magenta para transparência.** O "magenta puro" vira fundo em qualquer lugar, inclusive nos buracos entre as patas. As bordas passam por um **teste de mistura**: se o pixel está na reta entre a cor do fundo e a cor do animal ao lado, ele é franja. Se tem mais fundo que animal, vira transparente; se tem mais animal, recebe a cor do animal. Cores próprias do desenho não ficam nessa reta e são mantidas.
- A plumagem ameixa da Penala é avermelhada (r−b ≈ +58), enquanto a franja tem r ≈ b. Nenhuma seleção ampla de roxos foi usada.
- Um caso real conferido: na Penala há pontas de pena **rosa** encostando direto no fundo, sem contorno. Uma regra por cor teria apagado essas pontas. Com o teste de mistura, elas foram preservadas.
- Nenhuma pose foi cortada (nenhuma encosta na borda da folha) e nenhum pedaço solto foi encontrado.

**Escala.** As folhas não têm grade de pixels consistente (periodicidade ≈ 0,01), o que confirma o aviso do pacote. Por isso, a redução foi feita por **média de área com alpha pré-multiplicado**, seguida de **alpha binário** (sem semitransparência) e de **uma paleta fixa por espécie** (sem dithering), para as cores não "piscarem" entre quadros. Não houve bilinear, blur, upscale nem redimensionamento de pose individual.
- **As folhas de caminhada vieram de 9% a 21% maiores que as de ações.** Por isso há um fator por folha, calculado para o animal parado de lado ter a mesma altura nas duas.
- Cada pose é posicionada num canvas comum com o pivot no mesmo lugar, e só então o canvas inteiro é reduzido. Assim, todos os quadros usam a mesma grade de amostragem, o que evita tremor.

**Alinhamento.** Os pés ficam na linha de base (pivot). Na caminhada, o tronco é casado com o 1º quadro da direção. Nas ações, as patas são casadas com o 1º quadro de respirar/piscar, para as patas plantadas não deslizarem durante a ação.

### Especificação por espécie

| Espécie | Altura de lado (px) | Canvas (px) | Pivot | Redução caminhada | Redução ações | Caminhada maior em | Encaixe ações | Caminhada (quadros/s) | Velocidade sugerida (px/s) | Cores | Pose de parado (quadro) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| penala | 32 | 58×40 | 20, 38 | 0.167 | 0.200 | 20% | +1 | 10 | 30 | 32 | baixo 0, esquerda 6, direita 2, cima 0 |
| pato | 30 | 60×38 | 25, 36 | 0.163 | 0.194 | 19% | −1 | 9 | 22 | 32 | baixo 0, esquerda 1, direita 0, cima 0 |
| ovelha | 44 | 60×56 | 28, 54 | 0.251 | 0.274 | 9% | +1 | 7 | 26 | 28 | baixo 1, esquerda 1, direita 6, cima 0 |
| gruntho | 38 | 74×54 | 36, 52 | 0.235 | 0.284 | 21% | 0 | 8 | 32 | 28 | baixo 3, esquerda 1, direita 2, cima 0 |
| vaca | 54 | 96×84 | 48, 82 | 0.305 | 0.351 | 15% | +1 | 6 | 20 | 32 | baixo 2, esquerda 0, direita 1, cima 6 |

Os quadros são numerados a partir de 0.

- **As alturas são uma proposta** (protagonista ≈ 64 px, tile 48). Elas precisam ser conferidas com os animais que já estão no jogo. Para mudar, edite `ferramentas/escala_especies.json` e rode `rodar_tudo.py`.
- O canvas é grande porque comporta todas as poses da espécie (as asas abertas da Penala e do pato e a vista de frente da vaca, que é mais alta).
- **No Godot:** `centered = false` e `offset = -pivot`. Assim, a posição do nó é o ponto de contato com o chão.
- **Comparação de tamanho no terreno real do jogo:** `revisao/escala_no_jogo.png`.

## 3. Arquivos

```
JogoFazenda/arte/preparado/fauna/
  fauna_index.json
  <especie>/<especie>_atlas.png   RGBA, uma linha por animação, células do tamanho do canvas
  <especie>/<especie>.json        célula, pivot, linhas, quadros, durações, loop, alertas
JogoFazenda/testes/fauna/
  carregador_fauna.gd   monta SpriteFrames a partir do JSON (reutilizável)
  teste_fauna.tscn/.gd  cena de teste
  verificar_fauna.gd    verificação automática sem abrir o editor
revisao/        pranchas (v2), comparação v1 x v2 (GIFs), prints da cena no Godot, medidas, v1/ (atlas antigos)
ferramentas/    scripts para refazer tudo a partir das folhas originais
visualizador/   bancada_fauna.html (abre no navegador, inclusive no celular; botão v1/v2)
```

Os arquivos ficam em `arte/preparado/`, não em `arte/final/`, porque ainda não foram validados dentro do jogo. **Nada substitui os animais atuais.**

**Importação no Godot:** confira na aba Import que os atlas estão com filtro Nearest, sem mipmaps e com compressão sem perdas (Lossless). A cena de teste força Nearest em cada nó.

## 4. Tempos e velocidade

- **Caminhada:** penala 10, pato 9, gruntho 8, ovelha 7 e vaca 6 quadros/s. Animais menores dão passos mais rápidos. São pontos de partida para testar.
- **Velocidade de deslocamento:** a medida pelo pé apoiado **não é confiável nestes ciclos**. O pé no chão não recua de forma regular entre os quadros (a direção muda de um quadro para outro), então nenhuma velocidade elimina todo o escorregão. Os valores da tabela são iniciais. Ajuste a olho com o controle "Chão andando".
- **Respirar/piscar:** segura o quadro 0 por um tempo aleatório entre 1,5 s e 4 s e então toca o gesto. Não pisca o tempo todo.
- **Ações:** antecipação curta, gesto principal mais longo e recuperação. As durações por tipo estão no JSON: cabeça baixa (pastar, beber, bicar, fuçar), voz, sacudir e asas. Ruminar e mastigar repetem 3×, e mover a cauda repete 2×. No modo natural, elas aparecem com intervalos aleatórios de 4 a 12 s. **Nenhuma regra de jogo (necessidades, produção) foi tocada.**
- Nada foi acelerado e nenhum quadro foi duplicado para esconder defeitos.

## 5. Defeitos e decisões

### ❌ Ainda exigem redesenho
| Animal | Animação | Direção | Quadros | Problema | Correção necessária |
|---|---|---|---|---|---|
| Vaca | caminhada | esquerda e direita | todos | Vista 3/4 e corpo curto (largura ≈ altura); as ações são de perfil e compridas (largura ≈ 1,5× a altura). A vaca muda de forma ao passar de andar para uma ação. | Redesenhar a caminhada lateral de perfil, com as mesmas proporções das ações (ou as ações em 3/4) |
| Vaca | caminhada | cima | 1→2 | Cabeça e chifres crescem e sobem cerca de 4 px. As manchas variam mais que nas outras direções (≈10%). | Redesenhar o quadro 2 (e conferir 3–7) mantendo o tamanho da cabeça |
| Pato | caminhada | cima | 0, 4, 6 | A cabeça fica 2–3 px mais baixa nesses quadros, de forma irregular | Redesenhar com um sobe e desce regular |
| Gruntho | caminhada | cima | 3, 7 | **Corrigido provisoriamente na v2** (a pata esquerda levanta por transplante espelhado) | Um redesenho com alternância desenhada ficaria melhor |

### ⚠ Atenção
| Animal | Animação | Situação na v2 |
|---|---|---|
| Penala | caminhada para baixo e para cima | Pausas encurtadas (quadros 0 e 7; 0 e 3) |
| Ovelha | caminhada para cima | Pausas encurtadas (quadros 3 e 7) |
| Gruntho | caminhada para baixo | O passo aparece só nos quadros 1 e 4; o quadro 2 (quase repetido) foi encurtado |
| Vaca | caminhada para a direita | Topo sobe cerca de 4 px do quadro 0 para o 1 (desenhado assim); quadros 3 e 4 encurtados |

As "ordens alternativas" sugeridas pela medida automática (no JSON) foram calculadas por menor movimento entre quadros. **Elas não foram aplicadas**: num ciclo de passos, a ordem com menos movimento nem sempre é a correta. A ordem original foi mantida.

### Decisões pendentes
1. **Ações para a esquerda:** só existem viradas para a direita. Espelhar inverte a luz (que vem de cima à esquerda). É preciso decidir entre espelhar ou desenhar o lado esquerdo. A cena de teste tem a opção "Espelhar ações (teste)", desligada por padrão.
2. **Parado de frente e de costas:** não há respirar/piscar nessas direções. Por enquanto, segura a pose de parado da caminhada (patas juntas).
3. **Tamanhos finais:** confirmar com os animais atuais do jogo.
4. **Fora deste pacote** (não improvisado): sono, repouso, levantar, nado e a segunda ave aquática.

## 6. Cena de teste

Abra `res://testes/fauna/teste_fauna.tscn` e aperte F6.
- Seleção de animal (ou "Comparar os 5"), animação e ação; tocar, pausar e quadro a quadro; velocidade; zoom inteiro.
- Fundo terreno, claro ou escuro. Para usar o chão real, arraste a textura do jogo para `textura_terreno` no Inspetor.
- "Chão andando", para ver se os pés escorregam. "Pivot e caixa", "Modo natural" e "Espelhar ações (teste)".
- **Teclado:** setas/WASD para andar (testa as transições), E para a ação, Espaço para pausar, vírgula e ponto para ir quadro a quadro.
- Ao soltar as setas, o animal para na pose de parado da direção. Ao andar de novo, começa do quadro seguinte.

**Verificação automática** (sem abrir o editor):
```
godot --headless --path <pasta do projeto> --script res://testes/fauna/verificar_fauna.gd
```
Resultado obtido aqui, no Godot 4.5: **PASSOU, 117 de 117** (3 rodadas seguidas). Entre os testes: ao parar, segura a pose de parado da direção, e ao voltar a andar começa do quadro seguinte.
