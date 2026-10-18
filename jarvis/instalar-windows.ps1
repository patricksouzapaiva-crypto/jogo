# Instala e configura o Ryan (Hermes Agent + Claude Code) para o jogo, no Windows.
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

Add-Type -AssemblyName System.Windows.Forms

if (-not $Projeto) {
  Write-Host "Escolha na janela a pasta do seu jogo (onde fica o arquivo project.godot)..." -ForegroundColor Cyan
  $dialogo = New-Object System.Windows.Forms.FolderBrowserDialog
  $dialogo.Description = "Escolha a pasta do seu jogo (onde fica o arquivo project.godot)"
  if ($dialogo.ShowDialog() -ne "OK") { throw "Nenhuma pasta escolhida." }
  $Projeto = $dialogo.SelectedPath
}
if (-not (Test-Path $Projeto -PathType Container)) { throw "Pasta não encontrada: $Projeto" }
$Projeto = (Resolve-Path $Projeto).Path
if (-not (Test-Path (Join-Path $Projeto "project.godot"))) { Aviso "Não achei project.godot em $Projeto (continuando mesmo assim)." }

$GodotBin = [Environment]::GetEnvironmentVariable("GODOT_BIN", "User")
if (-not $GodotBin -or -not (Test-Path $GodotBin)) {
  Write-Host "Agora escolha na janela o executável do Godot que termina em _console.exe..." -ForegroundColor Cyan
  $arquivo = New-Object System.Windows.Forms.OpenFileDialog
  $arquivo.Title = "Escolha o Godot (o arquivo que termina em _console.exe)"
  $arquivo.Filter = "Godot console (*console.exe)|*console.exe|Todos os programas (*.exe)|*.exe"
  if ($arquivo.ShowDialog() -eq "OK") {
    $GodotBin = $arquivo.FileName
    [Environment]::SetEnvironmentVariable("GODOT_BIN", $GodotBin, "User")
    Write-Host "Godot registrado: $GodotBin"
  } else {
    Aviso "Godot não escolhido. Depois rode: setx GODOT_BIN `"C:\caminho\Godot_..._console.exe`""
  }
}
$env:GODOT_BIN = $GodotBin

Passo "1/6 Verificando o Git"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
  Recarregar-Path
}
if (-not (Test-Path (Join-Path $Projeto ".git"))) {
  git -C $Projeto init -q
  if (-not (git config --global user.name)) {
    git -C $Projeto config user.name "Ryan"
    git -C $Projeto config user.email "ryan@localhost"
  }
  git -C $Projeto add -A
  git -C $Projeto commit -qm "Estado inicial antes do Ryan"
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

Passo "4/6 Identidade e skills do Ryan"
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

Passo "Ligando o cérebro grátis (Nous Portal)"
Write-Host "Siga as perguntas abaixo. Se pedir login, uma página vai abrir no navegador."
hermes setup --portal

Write-Host @"

Pronto! O Ryan está instalado. Próximos passos (quando quiser):

  1. hermes fallback add       # reserva grátis: OpenRouter -> um modelo terminado em :free
                               # (chave grátis em https://openrouter.ai/keys)
  2. hermes config edit        # cole os blocos de $Kit\hermes\config-jarvis.yaml (regras de segurança)
  3. claude                    # (só se tiver Claude Pro/Max) login no Claude Code
  4. hermes gateway setup      # conecte o Telegram ou o WhatsApp
     hermes gateway start
  5. hermes computer-use       # (opcional) controle da tela
  6. Edite $Projeto\AGENTS.md com a visão do seu jogo.

Teste agora: feche esta janela, abra um PowerShell novo, digite  hermes  e escreva:
  Ryan, roda o teste do jogo e me diz se tem erro.
"@ -ForegroundColor Green
