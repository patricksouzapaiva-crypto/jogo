---
name: video-devlog
description: Cria vídeos curtos de divulgação do jogo (devlog para Reels, TikTok e Shorts) com o MoneyPrinterTurbo, em português, usando de preferência clipes reais do jogo gravados pelo Patrick.
version: 1.0.0
metadata:
  hermes:
    tags: [video, divulgacao, devlog]
    category: jogo
    requires_toolsets: [terminal]
---

# Vídeo de devlog com o MoneyPrinterTurbo

## When to Use
Quando o Patrick pedir um vídeo do jogo: "faz o vídeo do devlog de hoje", "cria um Reels mostrando o
sistema de plantio", "instala o MoneyPrinterTurbo".

## Procedure
1. **Instalação e geração seguem a skill oficial do projeto.** Baixe e siga:
   https://raw.githubusercontent.com/harry0703/MoneyPrinterTurbo/main/docs/skill/SKILL.md
   (ela usa o ajudante `mpt_agent.py` e o `uv`; não use o pacote "MoneyPrinterTurbo" do PyPI, que é de terceiros).
2. **Sobrescreva os padrões dela** (que são em chinês) passando opções extras depois de `--`.
   Confira os nomes exatos uma vez com `cli.py --help` e use:
   - idioma do roteiro: português do Brasil (`pt-BR`);
   - voz Edge TTS: `pt-BR-AntonioNeural` (ou `pt-BR-FranciscaNeural`);
   - formato `9:16`; legendas no modo `edge` (o modo `whisper` é pesado demais para este PC).
3. **Imagens:** se existir a pasta `gravacoes/` (ou a que o Patrick indicar) com clipes do jogo,
   use esses arquivos locais como material do vídeo. Só use Pexels/Pixabay se ele pedir ou se não
   houver clipes, e nesse caso avise que o vídeo não vai mostrar o jogo.
4. **Roteiro:** curto (20 a 40 s), tom de diário de desenvolvimento: o que foi feito, por que é
   legal, chamada para seguir o perfil. Baseie-se nos commits recentes (`git log --since="7 days ago"`).
5. **Provedores grátis:** para o roteiro, reutilize o OpenRouter `:free` já configurado; para
   Pexels/Pixabay, chave grátis. Nunca ative opções pagas (flags `--confirm-*-charge`).
6. **Música:** não use as faixas padrão do projeto (vêm do YouTube e podem gerar problema de
   direitos autorais). Use música livre que o Patrick colocar numa pasta, ou sem música.
7. Entregue o caminho do MP4 final e um resumo de 1 frase. **Nunca publique** em rede social sem o
   Patrick aprovar o vídeo.

## Pitfalls
- A geração demora vários minutos nesta máquina: rode em segundo plano e avise o Patrick.
- Nunca mostre chaves de API nem o conteúdo do `config.toml`.

## Verification
O arquivo `final-1.mp4` existe, tem narração em português e mostra o jogo (quando havia clipes).
