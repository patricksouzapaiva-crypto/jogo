# Prompt para o chat principal (colocar o herói novo no jogo)

**Antes de colar:** baixe a pasta `heroi_preparado/` do GitHub (repositório **jogo**, branch
`claude/conversa-perdida-nuvem-26xpxi`) e coloque dentro da pasta do projeto, ao lado de `JogoFazenda/`.
Depois cole o texto abaixo no chat principal.

```
Preparei fora do projeto as animações novas do herói (protagonista): andar nas
4 direções (8 quadros cada, 75 ms) e parado respirando (2 quadros), feitas com a
técnica de "esqueleto" a partir do turnaround. Está tudo em heroi_preparado/.
Leia primeiro heroi_preparado/LEIA_PRIMEIRO_HEROI.md.

1. INSPECIONE O PROJETO ANTES DE MEXER
- Ache o personagem do jogador: cena, script, AnimatedSprite2D (ou Sprite2D),
  nomes das animações que ele usa hoje, velocidade de movimento, colisão e y-sort.
- Faça backup (commit ou cópia) do personagem atual para comparação e para voltar atrás.
- Não crie um sistema paralelo: adapte ao que já existe.

2. COPIE SEM SUBSTITUIR NADA
- Copie heroi_preparado/JogoFazenda/arte/preparado/heroi/ e
  heroi_preparado/JogoFazenda/testes/heroi/ para as mesmas pastas do projeto
  (res://arte/preparado/heroi e res://testes/heroi).
- Importação do heroi_atlas.png: filtro Nearest, sem mipmaps, compressão Lossless.
- Rode a verificação:
  godot --headless --path . --script res://testes/heroi/verificar_heroi.gd
  (fora do projeto deu TUDO OK, 35 de 35).
- Abra res://testes/heroi/teste_heroi.tscn e rode (setas/WASD andam, Espaço liga/desliga
  a demonstração). Coloque a textura do chão do jogo em "textura_terreno" para ver no terreno real.

3. TROQUE A ARTE DO HERÓI, SÓ DEPOIS DA MINHA APROVAÇÃO NA CENA DE TESTE
- Use CarregadorHeroi.preparar_sprite(sprite, CarregadorHeroi.carregar()) ou monte um
  SpriteFrames a partir do heroi.json (cada quadro tem a sua duração; velocidade da animação = 1).
- Pivô no chão: centered = false e offset = -pivot (24, 69). A posição do nó passa a ser o
  ponto entre os pés: confira colisão e y-sort com esse ponto.
- Célula 48×72, mesmo tamanho do personagem atual. Não estique nem redimensione.
- Nomes: walk_down, walk_left, walk_right, walk_up, idle_down, idle_left, idle_right, idle_up.
  Se o código usa outros nomes, adapte o código (não renomeie a folha).

4. COMPORTAMENTO
- Parado: idle_<direção> da última direção em que andou (respirando).
- Começar a andar: walk_<direção> a partir do quadro "inicio" do JSON.
- Trocar de direção andando: mantenha o número do quadro (o passo continua sem tranco).
- Parar: idle_<direção> a partir do quadro 0.
- Não reinicie a animação a cada atualização (só quando muda de animação).
- Velocidade: 47 px/s deixa os pés sem escorregar. Se o jogo usa outra velocidade,
  mantenha a do jogo e use speed_scale = velocidade / 47 no AnimatedSprite2D.
  Me diga qual velocidade o jogo usa.
- Pixel nítido: posição do sprite arredondada (ou "snap 2D transforms to pixel").
- Não mude nenhuma outra regra do jogo.

5. ME MOSTRE O RESULTADO
- Tire uma foto (ou grave) o herói andando nas 4 direções e parado no jogo.
- Liste o que mudou e como voltar atrás.
- Ações com ferramentas, correr e dormir ainda não fazem parte deste pacote.

Explique tudo em linguagem simples.
```
