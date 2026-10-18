#!/usr/bin/env bash
# Instala e configura o Jarvis (Hermes Agent + Claude Code) para o jogo, no macOS, Linux ou WSL2.
# Uso:  bash jarvis/instalar-mac-linux.sh "/caminho/para/o/projeto-do-jogo"
set -euo pipefail

KIT="$(cd "$(dirname "$0")" && pwd)"
PROJETO="${1:-}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

passo() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
aviso() { printf '\033[1;33m[!] %s\033[0m\n' "$1"; }

if [ -z "$PROJETO" ]; then
  read -r -p "Caminho da pasta do projeto do jogo (onde fica o project.godot): " PROJETO
fi
PROJETO="${PROJETO/#\~/$HOME}"
[ -d "$PROJETO" ] || { echo "Pasta não encontrada: $PROJETO"; exit 1; }
PROJETO="$(cd "$PROJETO" && pwd)"
[ -f "$PROJETO/project.godot" ] || aviso "Não achei project.godot em $PROJETO (continuando mesmo assim)."

passo "1/6 Verificando o Git"
command -v git >/dev/null || { echo "Instale o Git primeiro: https://git-scm.com/downloads"; exit 1; }
if [ ! -d "$PROJETO/.git" ]; then
  git -C "$PROJETO" init -q
  git -C "$PROJETO" add -A
  git -C "$PROJETO" commit -qm "Estado inicial antes do Jarvis" || true
  echo "Repositório Git criado no projeto (rede de segurança para desfazer mudanças)."
fi

passo "2/6 Claude Code"
if command -v claude >/dev/null; then
  echo "Já instalado: $(claude --version)"
else
  curl -fsSL https://claude.ai/install.sh | bash
fi

passo "3/6 Hermes Agent"
if command -v hermes >/dev/null; then
  echo "Já instalado."
else
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  # O instalador adiciona o hermes ao PATH no ~/.bashrc / ~/.zshrc; carrega para esta execução.
  export PATH="$HOME/.local/bin:$HERMES_HOME/bin:$PATH"
fi
command -v hermes >/dev/null || { aviso "Abra um terminal novo e rode este script de novo."; exit 1; }

passo "4/6 Identidade e skills do Jarvis"
mkdir -p "$HERMES_HOME/skills"
if [ -f "$HERMES_HOME/SOUL.md" ] && ! cmp -s "$HERMES_HOME/SOUL.md" "$KIT/hermes/SOUL.md"; then
  cp "$HERMES_HOME/SOUL.md" "$HERMES_HOME/SOUL.md.bak"
  echo "SOUL.md anterior guardado em SOUL.md.bak"
fi
cp "$KIT/hermes/SOUL.md" "$HERMES_HOME/SOUL.md"
mkdir -p "$HERMES_HOME/skills/jogo"
cp -R "$KIT/hermes/skills/jogo/." "$HERMES_HOME/skills/jogo/"
echo "Skills instaladas: $(ls "$HERMES_HOME/skills/jogo" | tr '\n' ' ')"

passo "5/6 Arquivos de instruções no projeto do jogo"
for f in AGENTS.md CLAUDE.md .claude/settings.json; do
  if [ -e "$PROJETO/$f" ]; then
    echo "Mantido (já existe): $f"
  else
    mkdir -p "$(dirname "$PROJETO/$f")"
    cp "$KIT/projeto-do-jogo/$f" "$PROJETO/$f"
    echo "Criado: $f"
  fi
done
grep -qxF ".godot-teste.log" "$PROJETO/.gitignore" 2>/dev/null || echo ".godot-teste.log" >> "$PROJETO/.gitignore"

passo "6/6 Configuração do Hermes"
hermes config set approvals.mode smart
hermes config set terminal.cwd "$PROJETO"

cat <<EOF

Pronto! Agora faça estes passos (são interativos, por isso não estão no script):

  1. hermes setup              # escolha o modelo (veja "Qual modelo usar" no README)
  2. hermes config edit        # cole os blocos de $KIT/hermes/config-jarvis.yaml
  3. claude                    # rode uma vez para fazer login no Claude Code
  4. hermes gateway setup      # conecte o Telegram ou o WhatsApp
     hermes gateway start
  5. hermes computer-use       # (opcional) controle da tela
  6. Edite $PROJETO/AGENTS.md com a visão do seu jogo.

Teste: hermes  →  "Jarvis, roda o teste do jogo e me diz se tem erro."
EOF
