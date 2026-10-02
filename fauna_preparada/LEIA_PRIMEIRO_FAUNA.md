# Fauna preparada v1: relatório de preparação e teste

Origem: `MOVIMENTACOES_DOS_ANIMAIS_v1.zip` (as folhas de caminhada são idênticas às do `CAMINHADA_DOS_ANIMAIS.zip`; os hashes do manifesto conferem).
Espécies: Penala, pato anfíbio, ovelha, Gruntho e vaca. Ao todo, 340 poses: 5 × 32 de caminhada e 5 × 36 de ações.

**Situação:** os quadros estão preparados e a cena de teste roda no Godot 4.5 (116 de 116 verificações automáticas passaram). **A integração com o sistema de animais do jogo ainda não foi feita**, porque este trabalho foi feito fora do projeto. Isso fica para o chat principal (veja `PROMPT_CHAT_PRINCIPAL.md`). Há 3 defeitos que exigem redesenho e algumas decisões pendentes (abaixo).

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

| Espécie | Altura de lado (px) | Canvas (px) | Pivot | Redução caminhada | Redução ações | Caminhada maior em | Caminhada (quadros/s) | Velocidade sugerida (px/s) | Cores |
|---|---|---|---|---|---|---|---|---|---|
| penala | 32 | 58×40 | 21, 38 | 0.167 | 0.200 | 20% | 10 | 30 | 32 |
| pato | 30 | 60×38 | 24, 36 | 0.163 | 0.194 | 19% | 9 | 22 | 32 |
| ovelha | 44 | 60×56 | 29, 54 | 0.251 | 0.274 | 9% | 7 | 26 | 28 |
| gruntho | 38 | 74×54 | 36, 52 | 0.235 | 0.284 | 21% | 8 | 32 | 28 |
| vaca | 54 | 96×84 | 49, 82 | 0.305 | 0.351 | 15% | 6 | 20 | 32 |

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
revisao/        pranchas, prints da cena no Godot, medidas em JSON
ferramentas/    scripts para refazer tudo a partir das folhas originais
visualizador/   bancada_fauna.html (abre no navegador, inclusive no celular)
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

### ❌ Exigem redesenho
| Animal | Animação | Direção | Quadros | Problema | Correção necessária |
|---|---|---|---|---|---|
| Vaca | caminhada | esquerda e direita | todos | Vista 3/4 e corpo curto (largura ≈ altura); as ações são de perfil e compridas (largura ≈ 1,5× a altura). A vaca muda de forma ao passar de andar para uma ação. | Redesenhar a caminhada lateral de perfil, com as mesmas proporções das ações (ou as ações em 3/4) |
| Vaca | caminhada | cima | 1→2 | Cabeça e chifres crescem e sobem cerca de 4 px. As manchas variam mais que nas outras direções (≈10%). | Redesenhar o quadro 2 (e conferir 3–7) mantendo o tamanho da cabeça |
| Gruntho | caminhada | cima | 1, 3, 5, 7 | Só a pata traseira direita levanta; a esquerda quase não se move (≈5% de mudança nas patas). Vai parecer que ele desliza. | Redesenhar com alternância clara: esquerda nos quadros 1–3, direita nos quadros 5–7 |

### ⚠ Atenção (técnico ou de revisão)
| Animal | Animação | Problema | Sugestão |
|---|---|---|---|
| Penala | caminhada para baixo | Quadros 7, 0 e 1 quase iguais (pés juntos): pausa a cada ciclo | Redesenhar o quadro 0 como passagem, ou reduzir a duração de 7/0/1 depois de testar |
| Penala | caminhada para cima | Pares 0-1 e 3-4 muito parecidos | Revisar no visualizador |
| Ovelha | caminhada para cima | Quadros 3≈4 e 7≈0 | Revisar no visualizador |
| Gruntho | caminhada para baixo | O passo aparece só nos quadros 1 e 4 (ritmo irregular) | Revisar; talvez redesenhar 2 quadros |
| Vaca | caminhada para a direita | Topo sobe cerca de 4 px do quadro 0 para o 1 | Revisar no visualizador |

As "ordens alternativas" sugeridas pela medida automática (no JSON) foram calculadas por menor movimento entre quadros. **Elas não foram aplicadas**: num ciclo de passos, a ordem com menos movimento nem sempre é a correta. A ordem original foi mantida.

### Decisões pendentes
1. **Ações para a esquerda:** só existem viradas para a direita. Espelhar inverte a luz (que vem de cima à esquerda). É preciso decidir entre espelhar ou desenhar o lado esquerdo. A cena de teste tem a opção "Espelhar ações (teste)", desligada por padrão.
2. **Parado de frente e de costas:** não há respirar/piscar nessas direções. Por enquanto, segura o 1º quadro da caminhada.
3. **Tamanhos finais:** confirmar com os animais atuais do jogo.
4. **Fora deste pacote** (não improvisado): sono, repouso, levantar, nado e a segunda ave aquática.

## 6. Cena de teste

Abra `res://testes/fauna/teste_fauna.tscn` e aperte F6.
- Seleção de animal (ou "Comparar os 5"), animação e ação; tocar, pausar e quadro a quadro; velocidade; zoom inteiro.
- Fundo terreno, claro ou escuro. Para usar o chão real, arraste a textura do jogo para `textura_terreno` no Inspetor.
- "Chão andando", para ver se os pés escorregam. "Pivot e caixa", "Modo natural" e "Espelhar ações (teste)".
- **Teclado:** setas/WASD para andar (testa as transições), E para a ação, Espaço para pausar, vírgula e ponto para ir quadro a quadro.

**Verificação automática** (sem abrir o editor):
```
godot --headless --path <pasta do projeto> --script res://testes/fauna/verificar_fauna.gd
```
Resultado obtido aqui, no Godot 4.5: **PASSOU, 116 de 116**.
