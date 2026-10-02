# Medidas do protagonista (para calibrar os habitats)

## Números

| Medida | Valor |
|---|---|
| Altura do boneco (do pé ao topo do chapéu) | **64 px** |
| Largura do boneco parado de frente | **33 px** |
| Célula de cada quadro no atlas | **48 x 72 px** |
| Pivô (ponto do chão entre os pés, dentro da célula) | **(24, 69)** |
| Tile de referência usado nos pacotes | **48 x 48 px** (o herói tem cerca de 1,33 tile de altura) |
| Escala no Sprite2D / AnimatedSprite2D | **1 (escala 1:1)**: os PNG já estão no tamanho final. Não ampliar e não reduzir. |
| Filtro de textura | Nearest (pixel nítido), sem mipmaps |

Os animais preparados seguem a mesma régua: penala 32 px, pato 30 px, ovelha 44 px, gruntho 38 px, vaca 54 px (altura de lado).

## Arquivos

- `heroi_parado_frente_TAMANHO_REAL.png`: um quadro (48x72), igual ao do jogo.
- `heroi_4_direcoes_TAMANHO_REAL.png`: parado nas 4 direções, lado a lado.
- `heroi_atlas.png`: atlas completo (andar + parado, 4 direções).
- `heroi_com_grade_tile48_ampliado6x.png`: o herói sobre uma grade de tiles 48x48, ampliado 6x só para enxergar.

## Atenção

Estes números são do pacote preparado do herói, que foi feito para escala 1:1. O projeto Godot de verdade
está no seu computador. Se o chat principal mudou a escala do personagem, o zoom da câmera ou o tamanho
do tile, os números certos são os dele. Para confirmar, cole isto no chat principal:

```
Me passe, sem mudar nada no projeto:
1. O scale do Sprite2D/AnimatedSprite2D do personagem do jogador (e de algum nó pai, se tiver scale).
2. O zoom da Camera2D.
3. O tamanho do tile do TileMap/TileMapLayer (tile_size) e a resolução da janela (viewport).
4. Qual PNG/atlas o personagem usa agora (caminho res://).
5. Uma captura de tela do jogo com o personagem perto de uma cerca ou construção.
```
