# Herói — andar nas 4 direções + parado respirando (v1)

Tudo foi feito **fora do projeto do jogo**. Nada no jogo foi alterado.
O que fazer com isto: veja `PROMPT_CHAT_PRINCIPAL_HEROI.md`.

## 1. O que tem aqui

| Pasta / arquivo | O que é |
|---|---|
| `JogoFazenda/arte/preparado/heroi/heroi_atlas.png` | Folha final (384×576): 8 linhas de células 48×72 |
| `JogoFazenda/arte/preparado/heroi/heroi.json` | Animações, durações, pivô, velocidade e paleta |
| `JogoFazenda/testes/heroi/` | Carregador (`carregador_heroi.gd`), cena de teste (`teste_heroi.tscn`) e verificação automática (`verificar_heroi.gd`) |
| `revisao/heroi_final_4_direcoes.mp4` | Vídeo final: anda num quadrado e para respirando, depois as 4 direções de perto |
| `revisao/lado`, `lado_esq`, `frente`, `costas` | Quadros soltos, prancha, GIF e vídeo de cada direção |
| `revisao/godot/` | Fotos da cena de teste rodando no Godot 4.5 e o resultado da verificação |
| `fonte/` | Turnaround e as 4 poses com o fundo removido (de onde tudo sai) |
| `ferramentas/` | Scripts que geram tudo (`rodar_tudo.py` refaz o pacote inteiro) |

## 2. Números

- **Tamanho:** herói com **64 px de altura**, célula **48×72** (o mesmo tamanho do personagem atual do jogo).
- **Pivô:** (24, 69) = ponto do chão entre os pés. Use `centered = false` e `offset = -pivô`; assim a posição do nó é o pé.
- **Animações** (linhas da folha, nesta ordem): `walk_down`, `walk_left`, `walk_right`, `walk_up`, `idle_down`, `idle_left`, `idle_right`, `idle_up`.
- **Andar:** 8 quadros, **75 ms** cada (ciclo de 0,6 s).
- **Parado respirando:** 2 quadros (0,8 s com o peito em cima e 0,7 s com cabeça, tronco e braços 1 px mais baixos). As pernas não mexem.
- **Velocidade:** **47 px/s** = os pés não escorregam. Se o jogo precisar andar mais rápido, use `speed_scale = velocidade / 47` no AnimatedSprite2D (as pernas aceleram junto).
- **Começar a andar:** cada `walk_*` tem `inicio` no JSON (o quadro depois do mais parecido com o parado), para sair do parado sem tranco.
- **Virar andando:** todas as direções começam o passo com a mesma perna (quadro 0). Ao trocar de direção andando, mantenha o número do quadro.
- **Cores:** uma paleta só, de 32 cores, para as 4 direções. Alpha só 0 ou 255 (pixel nítido).

## 3. Como foi feito (técnica do "esqueleto")

A partir de **uma pose de cada direção** do turnaround, os scripts separam corpo, braços e pernas e montam o andar com uma perna de 2 partes (coxa e canela, com o joelho dobrando) e a bota girando. Tudo é feito no tamanho do desenho (9× maior) e só no fim reduzido para 64 px com paleta fixa e contorno escuro.

- **Lado direito:** coxa/canela com cinemática inversa, bota rola do calcanhar para a ponta, braço de perto balança com o cotovelo, perna e braço de longe são cópias mais escuras (o braço de longe só aparece na frente da barriga). Sobe e desce de 1–2 px.
- **Lado esquerdo:** mesma técnica e mesmo ciclo, mas **com o desenho do lado esquerdo** (medidas refeitas nele; as contas são feitas numa cópia virada e cada quadro é desvirado no fim, então todos os pixels são do desenho da esquerda).
- **Frente:** a perna que dá o passo dobra o joelho para a câmera (encurta, o pé sobe até 3 px e pisa mais para baixo), coxa com mais luz e canela com mais sombra; o corpo desce 1 px e passa o peso para a perna de apoio (a cabeça faz um caminho redondo de 1 px por quadro); braços da primeira versão (a mão desce/sobe e abre um pouco).
- **Costas:** o mesmo da frente, com o pé indo para cima na tela, a sola da bota aparecendo quando o pé sai do chão e a luz do joelho invertida.

Correções pedidas e aplicadas: costas retas quando o braço vai para a frente (sem corcunda, e com menos camisa atrás); bota sempre encaixada na calça (a barra da calça acompanha o ângulo da bota); andar de frente mais suave.

## 4. Verificação

- Godot 4.5 (sem abrir o editor): **35 de 35 OK** (`revisao/godot/verificacao_godot.txt`). Confere as 8 animações, quadros vazios, pés no chão, 75 ms, alpha sem meio-termo e as transições na cena de teste (parado → andar, troca de direção andando, parar e respirar, modo demonstração).
- `rodar_tudo.py` refaz os mesmos arquivos byte a byte.

## 5. Para depois (não está no pacote)

- Correr, ações com ferramentas (enxada, regador, machado...), sentar, dormir.
- O andar de frente/costas é mais discreto que o de lado (normal nessas vistas).
