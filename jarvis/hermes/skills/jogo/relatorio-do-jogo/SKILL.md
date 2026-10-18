---
name: relatorio-do-jogo
description: Monta um resumo do andamento do jogo (commits recentes, pendências do AGENTS.md/TODO, erros do último teste) e sugere as próximas 3 tarefas. Usado na rotina diária.
version: 1.0.0
metadata:
  hermes:
    tags: [godot, rotina, relatorio]
    category: jogo
    requires_toolsets: [terminal]
---

# Relatório do jogo

## When to Use
Na rotina agendada (cron) diária, ou quando o Patrick perguntar "como está o jogo?", "o que falta?".

## Procedure
1. Na pasta do projeto, colete:
   - `git log --since="1 day ago" --oneline` (o que mudou desde ontem);
   - `git status --short` (algo pendente sem commit);
   - a seção "Pendências" do `AGENTS.md` e o arquivo `TODO.md`, se existir.
2. Rode a skill `godot-testar` e anote se há erros.
3. Escreva o relatório em até 10 linhas:
   - ✅ o que avançou;
   - ⚠️ erros ou pendências;
   - 🎯 as próximas 3 tarefas sugeridas, da mais importante para a menos importante.
4. Termine perguntando qual das 3 o Patrick quer que você comece.

## Pitfalls
- Não execute as tarefas sugeridas sem o Patrick escolher (o relatório só sugere).

## Verification
O relatório foi entregue na plataforma configurada (Telegram/WhatsApp).
