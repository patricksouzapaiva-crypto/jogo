---
name: godot-testar
description: Testa o projeto Godot 4 sem abrir a janela (headless) - reimporta recursos, abre o projeto e roda a cena principal por alguns segundos, coletando erros de script.
version: 1.0.0
metadata:
  hermes:
    tags: [godot, testes]
    category: jogo
    requires_toolsets: [terminal]
---

# Testar o projeto Godot

## When to Use
Depois de qualquer mudança no jogo, ou quando o Patrick pedir "testa", "roda o jogo", "tem erro?".

## Procedure
1. Descubra o executável do Godot: use a variável `GODOT_BIN` se existir; senão tente `godot`,
   `godot4` ou `Godot_v4*` no PATH. Se nada for encontrado, pergunte ao Patrick o caminho e
   sugira salvá-lo com `hermes config set` ou na variável `GODOT_BIN` do `.env` do Hermes.
2. Na raiz do projeto (onde está o `project.godot`), reimporte os recursos:
   ```bash
   "$GODOT_BIN" --headless --editor --quit --path .
   ```
3. Rode o jogo por ~10 segundos sem janela e guarde a saída:
   ```bash
   "$GODOT_BIN" --headless --path . --quit-after 600 2>&1 | tee .godot-teste.log
   ```
4. Procure problemas no log: linhas com `ERROR`, `SCRIPT ERROR`, `Parse Error`, `Failed to load`.
   ```bash
   grep -nE "ERROR|Parse Error|Failed to load" .godot-teste.log || echo "SEM ERROS"
   ```
5. Se o projeto tiver testes (pasta `tests/` com GUT ou gdUnit4), rode-os também conforme o `AGENTS.md`.
6. Para conferir algo visual (posição, animação, cor), aí sim abra o jogo com janela e use
   `computer_use` para tirar um print; feche o jogo depois.

## Pitfalls
- No Windows, o executável costuma ser `Godot_v4.x-stable_win64_console.exe`; use a versão
  `_console` para ver a saída no terminal.
- A primeira importação de um projeto grande demora; rode em segundo plano.
- `.godot-teste.log` não deve ser commitado (o `.gitignore` do projeto já ignora).

## Verification
Saída "SEM ERROS" no passo 4 (e testes verdes, se existirem).
