# Jarvis: assistente autônomo para criar o jogo

Kit para montar no seu computador um "Jarvis" que recebe ordens por voz, terminal, Telegram ou
WhatsApp, decide os passos sozinho e executa as tarefas do jogo de fazenda em Godot.

```
 Você (voz / Telegram / WhatsApp / terminal)
        │
        ▼
 ┌──────────────────────┐   tarefas de código    ┌──────────────────────┐
 │  Hermes Agent        │ ─────────────────────▶ │  Claude Code         │
 │  "Jarvis"            │   claude -p "..."      │  "engenheiro"        │
 │  memória, voz, cron, │ ◀───────────────────── │  edita cenas e .gd,  │
 │  mensagens, tela     │   resumo + commit      │  testa e commita     │
 └──────────────────────┘                        └──────────────────────┘
        │  godot --headless (testes)   │  computer_use (só quando precisa da tela)
        ▼
   Projeto do jogo (Git = botão de desfazer)
```

## O que tem aqui

| Arquivo | Para que serve |
|---|---|
| `instalar-windows.ps1` / `instalar-mac-linux.sh` | Instalam Hermes e Claude Code, copiam identidade e skills, configuram a pasta do jogo |
| `hermes/SOUL.md` | Personalidade e regras de segurança do Jarvis |
| `hermes/skills/jogo/claude-code-dev` | Ensina o Jarvis a delegar programação ao Claude Code e conferir o resultado |
| `hermes/skills/jogo/godot-testar` | Testa o jogo sem abrir janela e caça erros de script |
| `hermes/skills/jogo/relatorio-do-jogo` | Resumo diário do andamento + próximas 3 tarefas |
| `hermes/config-jarvis.yaml` | Regras de aprovação (o que é bloqueado sempre), MCP do Godot e voz |
| `projeto-do-jogo/` | `AGENTS.md`, `CLAUDE.md` e permissões do Claude Code, copiados para o projeto do jogo |

## Antes de começar

- **Godot 4** instalado (no Windows, guarde o caminho do executável `..._console.exe`).
- **Git** (o instalador do Windows instala via `winget` se faltar).
- Uma conta Claude (para o Claude Code) e um jeito de pagar o modelo do Hermes (veja abaixo).

## Instalação (passo a passo)

1. Baixe este repositório no seu computador (botão **Code → Download ZIP** no GitHub, ou `git clone`).
2. Rode o instalador:
   - **Windows, jeito fácil:** dê **duplo clique em `jarvis\INSTALAR-JARVIS.bat`**. Janelas vão pedir
     a pasta do jogo e o Godot (`_console.exe`), e no final ele já liga o cérebro grátis. Se o Windows
     mostrar "O Windows protegeu o computador", clique em **Mais informações → Executar assim mesmo**.
   - **Windows** (PowerShell, se preferir digitar):
     ```powershell
     powershell -ExecutionPolicy Bypass -File jarvis\instalar-windows.ps1 "C:\Jogos\MinhaFazenda"
     ```
   - **Mac / Linux / WSL2**:
     ```bash
     bash jarvis/instalar-mac-linux.sh ~/Jogos/MinhaFazenda
     ```
3. Siga os passos que o script imprime no final:
   1. `hermes setup`: escolha o provedor e o modelo.
   2. `hermes config edit`: cole os blocos de `hermes/config-jarvis.yaml`.
   3. `claude`: faça login no Claude Code uma vez.
   4. `hermes gateway setup` e `hermes gateway start`: conecte o Telegram (o app desktop do Hermes tem
      o botão **Create with QR**, que cria o bot e já libera só o seu usuário).
   5. `hermes computer-use` (opcional): instala o controle de tela.
   6. Preencha os campos ✏️ do `AGENTS.md` no projeto do jogo.
   7. Diga onde está o Godot: variável `GODOT_BIN` (Windows: `setx GODOT_BIN "C:\...\Godot_v4.x_console.exe"`;
      Mac/Linux: `export GODOT_BIN=...` no `~/.zshrc`/`~/.bashrc`). Depois reinicie o gateway.

O script não sobrescreve `AGENTS.md`, `CLAUDE.md` ou `.claude/settings.json` que já existam no
projeto, e guarda o `SOUL.md` anterior como `SOUL.md.bak`.

## Qual modelo usar no Hermes (importante para o bolso)

O Claude Code usa a sua assinatura do Claude. O Hermes é cobrado à parte:

- **Plano Pro**: o Hermes **não** pode usar a assinatura. Use uma `ANTHROPIC_API_KEY`
  (console.anthropic.com) ou o OpenRouter, ambos pagos por uso.
- **Plano Max**: o login OAuth no Hermes só consome **créditos extras** comprados, não o plano base.

Sugestão econômica: deixe o Hermes com um modelo rápido e barato (ele só coordena e conversa) e
deixe o trabalho pesado de código para o Claude Code, que já está na assinatura.
**Defina um limite de gasto mensal** no painel do provedor.

Dê ao Hermes a própria chave em vez de "emprestar" o login do Claude Code: os dois disputando
o mesmo login causam erros de autenticação.

## Modo 100% grátis

Dá para começar sem pagar nada além do que você já paga:

| Peça | Opção grátis | Limite |
|---|---|---|
| Cérebro do Hermes | **Nous Portal free tier**: `hermes setup --portal` | Limite de uso; quando estoura, espera liberar |
| | **OpenRouter, modelos `:free`**: chave grátis em https://openrouter.ai/keys, depois `hermes model` → OpenRouter → um modelo terminado em `:free` | Poucas dezenas de pedidos por dia |
| | **Ollama (no seu PC)**: https://ollama.com, depois `ollama pull qwen3` e `hermes model` → endpoint local `http://localhost:11434/v1` | Sem limite, mas exige placa de vídeo boa (8 GB+ de VRAM) e é mais fraco |
| Programação | Claude Code (já incluso se você tem Claude Pro/Max). Sem assinatura, o próprio Hermes programa | Modelos grátis erram mais em código |
| Voz, Telegram, cron, tela | Grátis | — |

**Configuração padrão do kit (pensada para PC sem placa de vídeo forte):** Nous Portal como
cérebro principal e OpenRouter `:free` como reserva automática. Os passos estão no final do instalador
e o bloco `fallback` está em `hermes/config-jarvis.yaml`. O Ollama fica de fora: sem GPU compatível
ele demoraria minutos por resposta.

**Godot em PC modesto:** crie ou abra o projeto com o renderizador **Compatibility**
(Projeto → Configurações → Renderização). Para 2D em pixel art ele é o ideal.

Para economizar os limites grátis, use o Telegram e o terminal para pedidos e deixe a rotina diária
(`cron`) desligada até ter um modelo pago.

## Como usar no dia a dia

- Terminal: `hermes`, e depois *"Jarvis, cria o sistema de regar plantas com o regador"*.
- Celular: mande a mesma frase (ou um áudio) para o bot no Telegram.
- Voz no computador: ative `wake_word` no config e diga *"hey hermes"*.
- Rotina diária às 9h, com o relatório no Telegram:
  ```bash
  hermes cron create "every 1d at 09:00" "Faça o relatório do jogo" --skill relatorio-do-jogo
  ```

## Segurança (leia)

- **Git é o botão de desfazer.** O Jarvis faz commit a cada etapa; `git log` mostra tudo e
  `git revert <commit>` desfaz.
- `approvals.mode: smart` deixa passar comandos de rotina e pergunta ou bloqueia os perigosos. A lista
  `approvals.deny` bloqueia sempre (force push, `rm -rf` na raiz, `--dangerously-skip-permissions`...).
- O bot do Telegram deve responder **só ao seu usuário** (`TELEGRAM_ALLOWED_USERS`).
- Não deixe senhas, banco ou carteiras acessíveis ao usuário que roda o Hermes. Para mais isolamento,
  rode o Hermes em outro usuário do sistema ou numa VM.
- Nunca use `approvals.mode: off` ou `--yolo` no seu computador pessoal.

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `hermes`/`claude` não encontrado | Feche e abra o terminal (o PATH muda após instalar) |
| Jarvis não acha o Godot | Defina `GODOT_BIN` e rode `hermes gateway stop` e `hermes gateway start` |
| Qualquer outro erro do Hermes | `hermes doctor` |
| Claude Code pedindo permissão demais | Adicione o comando em `.claude/settings.json` do projeto |

Documentação oficial: Hermes, https://hermes-agent.nousresearch.com/docs/; Claude Code, https://code.claude.com/docs
