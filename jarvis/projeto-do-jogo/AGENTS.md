# Jogo de fazenda (Godot 4): instruções para agentes

> Este arquivo é lido pelo Hermes (Jarvis) e, via `CLAUDE.md`, pelo Claude Code.
> Preencha os campos marcados com ✏️ e mantenha atualizado: é a "memória do projeto".

## Visão do jogo ✏️
- Gênero: simulação de fazenda em pixel art, visão de cima (top-down), estilo Stardew Valley.
- Nome provisório: ✏️
- Público e plataforma: ✏️ (PC / celular)
- O que torna o jogo único: ✏️

## Stack
- Engine: Godot 4.x ✏️ (versão exata)
- Linguagem: GDScript, com tipagem estática (`var vida: int = 3`).
- Arte: pixel art, tiles de 16x16 ✏️, personagem de ✏️ px, filtro de textura "Nearest".
- Mapas: TileMapLayer por camada (chão, transições, objetos, colisão), com y-sort nos objetos.
- Renderizador: **Compatibility** (OpenGL). O PC de desenvolvimento tem uma GeForce GT 730 (4 GB),
  i5-3570 e 16 GB de RAM: não troque para Forward+/Mobile, evite shaders pesados, partículas em
  GPU e efeitos 3D. Mire em 60 FPS nessa máquina.

## Estrutura de pastas
```
res://
├── cenas/        # .tscn (uma pasta por sistema: jogador/, mapa/, ui/, itens/)
├── scripts/      # .gd soltos que não pertencem a uma cena
├── recursos/     # .tres (itens, plantas, TileSets)
├── arte/         # sprites e tilesets (.png)
├── audio/
└── tests/        # testes (GUT ou gdUnit4) ✏️
```

## Regras de código
- Nomes de arquivos e nós em `snake_case`; classes com `class_name` em `PascalCase`.
- Uma responsabilidade por script; comunicação entre sistemas por sinais ou por um autoload `Eventos`.
- Nada de caminhos absolutos de nós frágeis (`get_node("../../..")`); use `@export` ou grupos.
- Toda mudança precisa abrir o projeto sem erros (`godot --headless --path . --quit-after 600`).
- Commits pequenos, em português, descrevendo o que mudou para o jogador.

## O que os agentes podem fazer sozinhos
- Criar e editar cenas, scripts, recursos e testes dentro deste repositório.
- Rodar o Godot em modo headless e os testes.
- Fazer commit local.

## O que precisa de confirmação do Patrick
- Mudar a visão, o estilo de arte ou mecânicas centrais.
- Apagar cenas ou sistemas inteiros.
- `git push`, instalar plugins/addons novos, mudar a versão do Godot.

## Pendências ✏️
- [ ] Movimento do personagem em 4 direções com animação
- [ ] Mapa inicial da fazenda com transições automáticas de terreno
- [ ] Sistema de plantio (arar, plantar, regar, colher)
