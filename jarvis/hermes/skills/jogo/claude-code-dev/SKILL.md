---
name: claude-code-dev
description: Entrega tarefas de programação do jogo Godot (cenas, GDScript, recursos, testes, bugs) ao Claude Code rodando na pasta do projeto, e confere o resultado.
version: 1.0.0
metadata:
  hermes:
    tags: [godot, codigo, claude-code]
    category: jogo
    requires_toolsets: [terminal]
---

# Programar o jogo com o Claude Code

## When to Use
Sempre que o pedido envolver criar, alterar ou corrigir algo no projeto do jogo: scripts `.gd`,
cenas `.tscn`, recursos `.tres`, TileSets, animações, UI, sistemas (inventário, plantio, clima...),
ou investigar um bug.

## Procedure
1. Vá para a pasta do projeto (é o `terminal.cwd` configurado; confira com `pwd` e `git status`).
   Se houver mudanças não commitadas que não são suas, pergunte antes de continuar.
2. Escreva um pedido completo e autossuficiente para o Claude Code, com:
   - o objetivo em uma frase;
   - o comportamento esperado (o que o jogador vê/faz);
   - restrições (arquivos que não podem mudar, estilo, resolução dos sprites);
   - o critério de pronto ("o projeto abre sem erros e a cena X roda").
3. Rode o Claude Code em modo não interativo, em segundo plano, porque pode demorar:
   ```bash
   claude -p "<pedido>" --permission-mode acceptEdits --max-turns 60
   ```
   Use `terminal(..., background=true)` e acompanhe com `process(action="wait")`.
   Para continuar a mesma conversa depois (ajustes, correções), use `claude -c -p "<ajuste>"`.
4. Leia a resposta final do Claude Code e confira com `git diff --stat` o que mudou.
5. Rode a skill `godot-testar`. Se houver erro, mande o erro de volta com `claude -c -p "..."`
   (no máximo 3 rodadas; depois disso, relate ao Patrick).
6. Faça commit com mensagem clara em português:
   `git add -A && git commit -m "<o que mudou>"`.
7. Relate em poucas linhas: o que foi feito, arquivos principais, resultado do teste.

## Pitfalls
- `claude: command not found`: o Claude Code não está no PATH do Hermes. Rode `claude --version`
  no terminal normal; se funcionar lá, reinicie o gateway (`hermes gateway stop` e `hermes gateway start`).
- Pedido vago gera código errado: sempre descreva o critério de pronto.
- O Claude Code pede permissão para um comando não liberado: liberar em `.claude/settings.json`
  do projeto, não com `--dangerously-skip-permissions`.
- Não rode duas instâncias do Claude Code na mesma pasta ao mesmo tempo.

## Verification
`git log -1` mostra o commit novo, `godot-testar` passou, e o relato foi enviado ao Patrick.
