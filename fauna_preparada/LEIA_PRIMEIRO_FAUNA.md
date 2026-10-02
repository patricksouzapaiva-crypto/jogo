# Fauna preparada v4: relatório de preparação e teste

Origem: `MOVIMENTACOES_DOS_ANIMAIS_v1.zip` (as folhas de caminhada são idênticas às do `CAMINHADA_DOS_ANIMAIS.zip`; os hashes do manifesto conferem).
Espécies: Penala, pato anfíbio, ovelha, Gruntho e vaca. Ao todo, 340 poses: 5 × 32 de caminhada e 5 × 36 de ações.

**Situação:** os quadros estão preparados e **os cinco animais andam com o esqueleto de patas (v4)**. A cena de teste roda no Godot 4.5 (117 de 117 verificações automáticas passaram). **A integração com o sistema de animais do jogo ainda não foi feita**, porque este trabalho foi feito fora do projeto. Isso fica para o chat principal (veja `PROMPT_CHAT_PRINCIPAL.md`). Restam só melhorias opcionais e decisões (abaixo).


---

## v4: o esqueleto de patas nos cinco animais

A técnica que deu certo no Gruntho e na vaca (v3) foi aplicada também à **ovelha, ao pato e à Penala**:
- **Ovelha (quadrúpede):** as quatro patas andam na sequência traseira → dianteira → traseira → dianteira. De lado, a pose-base é a de respirar/piscar (o mesmo desenho das ações). De frente e de costas, as patas alternam.
- **Pato e Penala (aves, duas pernas):** as pernas alternam meio ciclo uma da outra, ficando cerca de 60% do ciclo apoiadas e 40% no ar, com o pé levantado. De frente e de costas, o **pato ginga** para o lado do pé apoiado (cerca de 1 px, com os pés fixos no chão), e a Penala ginga de leve.
- **Pés no chão:** nas poses-base da ovelha e do pato havia um pé desenhado um pouco erguido (7 px na folha, no pato). Quando apoiado, esse pé agora estica até o chão.
- **Pose com os dois pés apoiados:** na ovelha de costas, no pato de frente e de costas e na Penala de frente e de costas, um pé estava mais alto em todos os quadros. A pose-base recebeu o espelho do pé apoiado (como já tinha sido feito no Gruntho de costas).
- **Corpo estável (vale para os cinco):** os 8 quadros de cada direção usam o mesmo recorte e não são realinhados pelo pé mais baixo. Assim, o corpo não afunda quando o pé de baixo levanta. Isso também tirou um deslocamento irregular de 1 px que existia no Gruntho e na vaca da v3. Agora o único movimento vertical é o sobe e desce regular de 1 px, nas 20 direções.
- **Pixels soltos:** as pontas de garra que se soltavam na redução (6 px na Penala) são removidas.

**Resultado:** encaixe entre andar e parado de 0,96 a 0,99 nos cinco (andar, parar e as ações usam o mesmo desenho). Godot 4.5: 117 de 117.

| Pose-base | Ovelha | Pato | Penala |
|---|---|---|---|
| De lado (direita) | respirar/piscar, quadro 0 | respirar/piscar, quadro 0 | respirar/piscar, quadro 0 |
| De lado (esquerda) | espelho da direita | espelho da direita | espelho da direita |
| De frente | caminhada, quadro 1 | caminhada, quadro 3 (pé direito espelhado) | caminhada, quadro 0 (pé direito espelhado) |
| De costas | caminhada, quadro 2 (pé esquerdo espelhado) | caminhada, quadro 2 (pé esquerdo espelhado) | caminhada, quadro 2 (pé direito espelhado) |

Comparação animada: `revisao/comparacoes/andar_antes_agora_ovelha_pato_penala.gif`. As versões anteriores ficam em `revisao/v1/`, `v2/` e `v3/`.

---

## v3: Gruntho e vaca com esqueleto de patas

**O problema (medido):** no Gruntho de lado, as patas da frente mudavam cerca de 42% por quadro e as de trás só cerca de 9%. Só a da frente andava. De costas, a pata direita estava desenhada levantada em todos os quadros. A vaca andava em 3/4, curta, enquanto as ações eram de perfil, compridas, e a cabeça subia, descia e mudava de tamanho de 2 a 4 px aos trancos.

**A solução:** como os desenhos não tinham um ciclo de patas correto, as caminhadas desses dois animais passaram a ser **geradas a partir de uma única pose limpa por direção**, na resolução da folha (cerca de 3–4× a do jogo), antes da redução para pixel art:
- **Patas marcadas à mão:** cada pata foi separada da pose pela linha do joelho e pelo contorno escuro, com pontos-semente.
- **Pata de longe completada:** a parte da pata de longe que ficava escondida atrás da pata de perto foi completada refletindo a textura dela própria. Assim não aparece fresta quando as patas se afastam.
- **De lado:** sequência de quadrúpede (traseira-esq → dianteira-esq → traseira-dir → dianteira-dir, cada uma 1/4 de ciclo depois da outra). Cada pata fica cerca de 60% do ciclo apoiada e 40% no ar, com o casco levantado.
- **De frente e de costas:** as duas patas visíveis levantam alternadamente (a direita nos quadros 2–3 e a esquerda nos 6–7).
- **Corpo, cabeça, manchas e cerdas:** são idênticos em todos os quadros, então nada cintila, pula ou muda de tamanho. O sobe e desce de 1 px da v2 é aplicado por cima.

| Pose-base | Gruntho | Vaca |
|---|---|---|
| De lado (direita) | respirar/piscar, quadro 0 (o mesmo desenho do parado) | respirar/piscar, quadro 0 (**de perfil**, o mesmo desenho das ações) |
| De lado (esquerda) | espelho da direita | espelho da direita |
| De frente | caminhada, quadro 3 | caminhada, quadro 4 (os dois cascos no chão) |
| De costas | caminhada, quadro 0, com a pata direita posta no chão (espelho da esquerda) | caminhada, quadro 6 |

**Resultado medido** (movimento das patas por quadro, de lado): Gruntho, frente de 42% → 16% e trás de 9% → 17% (equilibrado). Vaca, frente 16% e trás 18–19%. O encaixe entre andar e parado subiu de 0,89 para 0,96 no Gruntho e de 0,66 para 0,97 na vaca: andar, parar e as ações usam o mesmo desenho.

**Limites:** o movimento das patas é calculado, então é regular, mas mais simples que uma animação desenhada à mão. A esquerda é espelho da direita (a luz fica invertida). As regiões das patas estão em `ferramentas/rig_patas.py` (dicionário `RIG`) e podem ser ajustadas: `passo` = passada e `levanta` = altura do casco, em px da folha.

Comparação animada v2 × v3: `revisao/comparacoes/andar_v2_v3_gruntho_vaca.gif`. A v2 fica em `revisao/v2/` e a v1 em `revisao/v1/`.

---

## v2: o que melhorou no andar

A v1 continua em `revisao/v1/` para comparação, e o visualizador tem um botão v1/v2/v3. A v2 vale para todos os animais; na v3, o Gruntho e a vaca trocaram as caminhadas pelas do esqueleto de patas. Nada foi redesenhado e nenhuma parte do corpo foi recortada nem girada.

| Melhoria | Antes (v1) | Depois (v2) |
|---|---|---|
| **Sobe e desce do corpo** | Em 16 dos 20 ciclos o topo da cabeça ficava parado, o que dava cara de andar duro, "deslizando" | O corpo sobe 1 px na passagem, 2 vezes por ciclo (uma por passo), em ritmo regular. A fase segue os pés. A linha do quadril é duplicada (a perna "estica" 1 px) e os pés continuam no chão. A vaca e o pato de costas já tinham sobe e desce desenhado e foram mantidos. |
| **Pausas no ciclo** | Quadros quase repetidos ficavam o mesmo tempo que os outros. Exemplo: Penala para baixo, 0,20 s preso por ciclo | Quadros quase repetidos duram metade, e o tempo sobra para os outros (o ciclo continua com a mesma duração). Penala para baixo: 0,11 s. Ovelha para cima: de 0,29 s para 0,16 s |
| **Cintilação da textura** | De 38% a 66% dos pixels do corpo mudavam de tom à toa entre quadros | Penala de 11% a 17%, Gruntho de 25% a 35%, ovelha de 24% a 41%, pato de 29% a 46%. A vaca melhorou pouco (de 43% a 49%, porque o corpo dela se move mais entre quadros). Contorno, cabeça e cauda que mexem de verdade não são tocados. |
| **Gruntho de costas** | Só a pata traseira direita levantava | A esquerda também levanta, nos quadros 3 e 7 (correção provisória: a pata direita levantada foi espelhada para a esquerda sobre os quadros com as patas no chão; o corpo e a luz são os originais) |
| **Parar e voltar a andar** | Parado para baixo, para cima ou para a esquerda segurava o quadro 0 (às vezes no meio do passo) | Cada direção tem uma **pose de parado** (patas juntas, dois pés no chão, sem a subida do passo). Ao voltar a andar, a animação começa no quadro seguinte. |
| **Encaixe andar → ação** | Até 2 px de "pulo" quando o animal parava e virava para uma ação | As ações foram deslocadas para casar a silhueta com a caminhada para a direita (no máximo 1 px de diferença) |

Comparação animada: `revisao/comparacoes/andar_v1_v2_lado.gif` e `andar_v1_v2_frente.gif`.

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

| Espécie | Altura de lado (px) | Canvas (px) | Pivot | Redução caminhada | Redução ações | Caminhada maior em | Encaixe ações (IoU) | Caminhada (quadros/s) | Velocidade sugerida (px/s) | Cores | Pose de parado (quadro) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| penala | 32 | 58×40 | 21, 38 | 0.167 | 0.200 | 20% | 0 (0.97) | 10 | 30 | 32 | baixo 0, esquerda 4, direita 4, cima 0 |
| pato | 30 | 60×38 | 24, 36 | 0.163 | 0.194 | 19% | 0 (0.99) | 9 | 22 | 32 | baixo 0, esquerda 5, direita 4, cima 0 |
| ovelha | 44 | 60×55 | 29, 53 | 0.251 | 0.274 | 9% | 0 (0.96) | 7 | 26 | 28 | baixo 0, esquerda 0, direita 0, cima 0 |
| gruntho | 38 | 74×54 | 36, 52 | 0.235 | 0.284 | 21% | 0 (0.96) | 8 | 32 | 28 | baixo 0, esquerda 4, direita 5, cima 0 |
| vaca | 54 | 96×82 | 49, 80 | 0.305 | 0.351 | 15% | 0 (0.97) | 6 | 20 | 32 | baixo 0, esquerda 7, direita 7, cima 0 |

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
revisao/        pranchas (v4), comparações em GIF, prints da cena no Godot, medidas, v1/ v2/ v3/ (atlas antigos)
ferramentas/    scripts para refazer tudo a partir das folhas originais
visualizador/   bancada_fauna.html (abre no navegador, inclusive no celular; botão v4/v2/v1)
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

### Melhorias opcionais (nada bloqueia)
| Animal | O que poderia ficar melhor |
|---|---|
| Os cinco | Para a esquerda, a caminhada é o espelho da direita (a luz fica invertida). Um desenho próprio para a esquerda ficaria melhor. |
| Pato e Penala | A cabeça não faz o "vai e vem" típico de ave ao andar (o esqueleto move só as pernas e o corpo inteiro). |
| Os cinco | O movimento das patas é calculado: é regular, mas mais simples que uma animação desenhada à mão. |

### ✅ Resolvidos na v4
| Animal | Problema anterior | Situação |
|---|---|---|
| Pato | Caminhada para cima com a cabeça subindo e descendo de forma irregular | Corpo idêntico em todos os quadros; só o sobe e desce regular |
| Ovelha, pato, Penala | Patas e texturas variavam entre quadros (desenho da IA) | Mesma pose em todos os quadros; as patas seguem o ciclo |
| Os cinco | Corpo afundando 1 px aos trancos quando o pé mais baixo levantava | Mesmo recorte nos 8 quadros, sem realinhar pelos pés |

### ✅ Resolvidos na v3 (esqueleto de patas)
| Animal | Problema anterior | Situação |
|---|---|---|
| Gruntho | De lado, só a pata da frente mexia (frente 42%, trás 9%) | As 4 patas andam em sequência (16% e 17%) |
| Gruntho | De costas, a pata direita estava sempre levantada | As patas alternam; a pose-base tem os dois cascos no chão |
| Vaca | Caminhada lateral em 3/4, incompatível com as ações de perfil | Anda de perfil, com o mesmo corpo das ações |
| Vaca | Caminhada para cima: a cabeça crescia cerca de 4 px | Corpo idêntico em todos os quadros |
| Vaca | Cabeça subindo e descendo aos trancos (2–4 px) | Só o sobe e desce regular de 1 px |

### ⚠ Atenção
| Animal | Animação | Situação na v2 |
|---|---|---|
| Penala | caminhada para baixo e para cima | Pausas encurtadas (quadros 0 e 7; 0 e 3) |
| Ovelha | caminhada para cima | Pausas encurtadas (quadros 3 e 7) |

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
Resultado obtido aqui, no Godot 4.5, com a v4: **PASSOU, 117 de 117** (2 rodadas). Entre os testes: ao parar, segura a pose de parado da direção, e ao voltar a andar começa do quadro seguinte.
