# Colocar no jogo: personagem novo + animais novos

## Passo a passo (você faz)

1. **Baixe o pacote.** No navegador em que você entra no GitHub, abra este link (baixa um ZIP de uns 30 MB):
   https://github.com/patricksouzapaiva-crypto/jogo/archive/refs/heads/claude/conversa-perdida-nuvem-26xpxi.zip
2. **Extraia o ZIP.** Dentro dele tem uma pasta com duas pastas importantes: `heroi_preparado` e `fauna_preparada`.
3. **Copie essas duas pastas** para a pasta do jogo, **ao lado** da pasta `JogoFazenda` (não dentro dela).
4. **Cole o texto abaixo** no chat principal.
5. Quando ele mostrar as cenas de teste, olhe com calma e **só então** diga se aprova colocar no jogo.

## Texto para colar no chat principal

```
Preparei fora do projeto as animações novas do PERSONAGEM (herói) e dos ANIMAIS.
Coloquei duas pastas ao lado de JogoFazenda/:
- heroi_preparado/  -> herói andando nas 4 direções (8 quadros, 75 ms) + parado respirando
- fauna_preparada/  -> Penala, pato anfíbio, ovelha, Gruntho e vaca (andar v4 + parado + ações)
Se não achar as pastas, tente baixar com:
  git clone --depth 1 --branch claude/conversa-perdida-nuvem-26xpxi https://github.com/patricksouzapaiva-crypto/jogo.git
(fora da pasta do projeto). Se não conseguir, me peça para baixar o ZIP.

Leia antes de mexer em qualquer coisa:
- heroi_preparado/LEIA_PRIMEIRO_HEROI.md e heroi_preparado/PROMPT_CHAT_PRINCIPAL_HEROI.md
- fauna_preparada/LEIA_PRIMEIRO_FAUNA.md e fauna_preparada/PROMPT_CHAT_PRINCIPAL.md
Esses dois PROMPT_CHAT_PRINCIPAL têm os detalhes de cada pacote; siga-os junto com os passos abaixo.

1. BACKUP PRIMEIRO
- Faça um commit (ou uma cópia da pasta do projeto) antes de qualquer mudança, para eu poder voltar atrás.

2. INSPECIONE O PROJETO
- Ache o personagem do jogador e os animais: cenas, scripts, AnimatedSprite2D/AnimationPlayer,
  nomes das animações, velocidades, escala, pivô, colisão e y-sort.
- Não crie sistemas paralelos: adapte ao que já existe.

3. COPIE SEM SUBSTITUIR NADA
- heroi_preparado/JogoFazenda/arte/preparado/heroi/  -> res://arte/preparado/heroi/
- heroi_preparado/JogoFazenda/testes/heroi/          -> res://testes/heroi/
- fauna_preparada/JogoFazenda/arte/preparado/fauna/  -> res://arte/preparado/fauna/
- fauna_preparada/JogoFazenda/testes/fauna/          -> res://testes/fauna/
- Importação dos PNG: filtro Nearest, sem mipmaps, compressão Lossless.

4. RODE AS VERIFICAÇÕES (sem abrir o editor)
  godot --headless --path . --script res://testes/heroi/verificar_heroi.gd   (fora do projeto: 35 de 35 OK)
  godot --headless --path . --script res://testes/fauna/verificar_fauna.gd   (fora do projeto: 117 de 117 OK)
- Me diga o resultado. Se algo falhar, explique o porquê antes de corrigir.

5. ME MOSTRE AS CENAS DE TESTE E ESPERE MINHA APROVAÇÃO
- Rode res://testes/heroi/teste_heroi.tscn e res://testes/fauna/teste_fauna.tscn
  (coloque a textura do chão do jogo em "textura_terreno" nas duas).
- Tire fotos (ou grave) e me mostre: herói andando nas 4 direções e parado; cada animal andando
  e parado; o herói ao lado dos animais para eu conferir os tamanhos.
- NÃO troque nada no jogo antes de eu aprovar.

6. DEPOIS DA MINHA APROVAÇÃO: COLOQUE NO JOGO
- Herói: siga a parte 3 e 4 de heroi_preparado/PROMPT_CHAT_PRINCIPAL_HEROI.md
  (pivô nos pés, célula 48x72, walk_*/idle_*, começar o andar no quadro "inicio",
  manter o quadro ao virar andando, parado respirando ao soltar a tecla).
  Velocidade: 47 px/s deixa os pés sem escorregar; se o jogo usa outra, mantenha a do jogo e use
  speed_scale = velocidade / 47. Me diga qual velocidade o jogo usa.
- Animais: siga a parte 5 de fauna_preparada/PROMPT_CHAT_PRINCIPAL.md
  (pivô no chão, durações do JSON, parado da direção, sem mudar regras de necessidades/produção).
- Não mude controles nem nenhuma outra regra do jogo.
- Ações com ferramentas (enxada, regador, machado...) AINDA NÃO: estão sendo feitas.

7. TESTE NO JOGO DE VERDADE E ME TRAGA O RELATÓRIO
- Ande pela fazenda nas 4 direções, pare, vire; veja os animais andando e parados perto do herói.
- Me mande fotos/vídeo, a lista do que mudou, como voltar atrás e as decisões pendentes
  (velocidade do herói; seção 5 do LEIA_PRIMEIRO_FAUNA.md).

Explique tudo em linguagem simples.
```
