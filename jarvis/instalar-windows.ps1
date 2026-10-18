# Instala e configura o Jarvis (Hermes Agent + Claude Code) para o jogo, no Windows.
# Uso (PowerShell):
#   powershell -ExecutionPolicy Bypass -File jarvis\instalar-windows.ps1 "C:\caminho\do\projeto-do-jogo"
param([string]$Projeto)

$ErrorActionPreference = "Stop"
$Kit = $PSScriptRoot
$HermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA "hermes" }

function Passo($t) { Write-Host "`n==> $t" -ForegroundColor Cyan }
function Aviso($t) { Write-Host "[!] $t" -ForegroundColor Yellow }
function Recarregar-Path {
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
              [Environment]::GetEnvironmentVariable("Path", "Machine")
}

if (-not $Projeto) { $Projeto = Read-Host "Caminho da pasta do projeto do jogo (onde fica o project.godot)" }
if (-not (Test-Path $Projeto -PathType Container)) { throw "Pasta não encontrada: $Projeto" }
$Projeto = (Resolve-Path $Projeto).Path
if (-not (Test-Path (Join-Path $Projeto "project.godot"))) { Aviso "Não achei project.godot em $Projeto (continuando mesmo assim)." }

Passo "1/6 Verificando o Git"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
  Recarregar-Path
}
if (-not (Test-Path (Join-Path $Projeto ".git"))) {
  git -C $Projeto init -q
  git -C $Projeto add -A
  git -C $Projeto commit -qm "Estado inicial antes do Jarvis"
  Write-Host "Repositório Git criado no projeto (rede de segurança para desfazer mudanças)."
}

Passo "2/6 Claude Code"
if (Get-Command claude -ErrorAction SilentlyContinue) {
  Write-Host "Já instalado: $(claude --version)"
} else {
  irm https://claude.ai/install.ps1 | iex
  Recarregar-Path
}

Passo "3/6 Hermes Agent"
if (Get-Command hermes -ErrorAction SilentlyContinue) {
  Write-Host "Já instalado."
} else {
  iex (irm https://hermes-agent.nousresearch.com/install.ps1)
  Recarregar-Path
  $env:Path += ";" + (Join-Path $HermesHome "bin")
}
if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) { Aviso "Feche e abra o PowerShell e rode este script de novo."; exit 1 }

Passo "4/6 Identidade e skills do Jarvis"
New-Item -ItemType Directory -Force (Join-Path $HermesHome "skills\jogo") | Out-Null
$Soul = Join-Path $HermesHome "SOUL.md"
if (Test-Path $Soul) {
  Copy-Item $Soul "$Soul.bak" -Force
  Write-Host "SOUL.md anterior guardado em SOUL.md.bak"
}
Copy-Item (Join-Path $Kit "hermes\SOUL.md") $Soul -Force
Copy-Item (Join-Path $Kit "hermes\skills\jogo\*") (Join-Path $HermesHome "skills\jogo") -Recurse -Force
Write-Host "Skills instaladas: $((Get-ChildItem (Join-Path $HermesHome 'skills\jogo')).Name -join ' ')"

Passo "5/6 Arquivos de instruções no projeto do jogo"
foreach ($f in @("AGENTS.md", "CLAUDE.md", ".claude\settings.json")) {
  $destino = Join-Path $Projeto $f
  if (Test-Path $destino) {
    Write-Host "Mantido (já existe): $f"
  } else {
    New-Item -ItemType Directory -Force (Split-Path $destino) | Out-Null
    Copy-Item (Join-Path $Kit "projeto-do-jogo\$f") $destino
    Write-Host "Criado: $f"
  }
}
$Gitignore = Join-Path $Projeto ".gitignore"
if (-not ((Test-Path $Gitignore) -and (Select-String -Path $Gitignore -Pattern '^\.godot-teste\.log$' -Quiet))) {
  Add-Content $Gitignore ".godot-teste.log"
}

Passo "6/6 Configuração do Hermes"
hermes config set approvals.mode smart
hermes config set terminal.cwd $Projeto

Write-Host @"

Pronto! Agora faça estes passos (são interativos, por isso não estão no script):

  1. hermes setup --portal     # cérebro grátis: Nous Portal (sem chave)
  2. hermes fallback add       # reserva grátis: OpenRouter -> um modelo terminado em :free
                               # (chave grátis em https://openrouter.ai/keys)
     hermes config edit        # cole os blocos de $Kit\hermes\config-jarvis.yaml
  3. claude                    # (só se tiver Claude Pro/Max) login no Claude Code
  4. hermes gateway setup      # conecte o Telegram ou o WhatsApp
     hermes gateway start
  5. hermes computer-use       # (opcional) controle da tela
  6. Edite $Projeto\AGENTS.md com a visão do seu jogo.
  7. Defina GODOT_BIN com o caminho do Godot (versão _console), por exemplo:
     setx GODOT_BIN "C:\Godot\Godot_v4.4-stable_win64_console.exe"

Teste: hermes  ->  "Jarvis, roda o teste do jogo e me diz se tem erro."
"@ -ForegroundColor Green
