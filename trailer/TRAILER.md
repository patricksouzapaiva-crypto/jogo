# Manual de produção: vídeo de atualização do jogo

> **Para o Claude Code rodando no PC do Patrick.** Siga este manual de ponta a ponta, sem pedir
> para o Patrick mexer em nada. Ele só informa **qual atualização** o vídeo mostra e aprova o
> resultado. Explique em português simples o que está fazendo, em uma linha por etapa.

## O PC (limites que mandam nas escolhas)
- Windows, i5-3570, 16 GB de RAM, GeForce GT 730 (4 GB, sem CUDA útil). **Sem IA pesada local.**
- Godot 4 no renderizador Compatibility. Jogo de fazenda em pixel art 2D.
- Tudo grátis. Nada de API paga, nunca ative opções que cobram.

## Meta de qualidade (o que "não robótico" quer dizer)
- **Cenas reais do jogo**, gravadas sem travar, com câmera de cinema. Nada de banco de imagens genérico.
- **Corte no ritmo da música** (troca de cena nas batidas), tomadas de 1,5 a 3 s, nunca mais de 4 s parado.
- **Narração humana**: frases curtas, pausas, energia variando. No máximo 1 frase por tomada.
- **Legenda bonita**: palavra destacada no tempo da fala, 2 a 4 palavras por vez, fonte grossa com
  contorno, sempre na área segura (longe das bordas e da interface do Reels/TikTok).
- **Áudio bem mixado**: música abaixa quando a narração fala (ducking), volume final em -14 LUFS.
- Abertura forte nos **3 primeiros segundos** e fechamento com logo e chamada ("Siga para acompanhar").

## Estrutura de pastas (dentro da pasta do jogo)
```
trailer/
├── roteiro.md            # roteiro aprovado desta atualização
├── trailer.tscn          # cena de gravação (mapa + câmera de trailer)
├── gravacoes/            # clipes .avi/.mp4 gravados pelo Movie Maker
├── narracao/             # narracao.wav + legendas.json (tempo de cada palavra)
├── musica/               # trilha livre de direitos
└── saida/                # vídeos finais: vertical 1080x1920 e horizontal 1920x1080
```
Adicione `trailer/gravacoes/`, `trailer/narracao/` e `trailer/saida/` ao `.gitignore` do jogo.

## Etapa 1: Instalar o que falta (uma vez)
Verifique antes de instalar; instale só o que faltar, com `winget` quando possível:
- **FFmpeg** (`winget install Gyan.FFmpeg`), **Node.js LTS** (`winget install OpenJS.NodeJS.LTS`),
  **Python 3.11** (`winget install Python.Python.3.11`), **Git**, **espeak-ng** (necessário ao Kokoro
  em português; instalador oficial em https://github.com/espeak-ng/espeak-ng/releases).
- Num ambiente virtual Python em `trailer\.venv`: `kokoro`, `soundfile`, `faster-whisper`.
- **OpenMontage**: clone https://github.com/calesthio/OpenMontage numa pasta própria (fora do jogo)
  e siga o README para Windows (`venv`, `pip install -r requirements.txt`, `npm install` em
  `remotion-composer`). Se `npm install` falhar com `ERR_INVALID_ARG_TYPE`, use `npx --yes npm install`.
  Não configure nenhuma chave paga; deixe a geração de vídeo por IA desligada.

## Etapa 2: Roteiro
1. Leia `git log --since="14 days ago"` e o `AGENTS.md` do jogo para entender a atualização.
2. Escreva `trailer/roteiro.md` seguindo `trailer/roteiro-modelo.md`: 30 a 45 s, 6 a 10 tomadas,
   cada uma com o que aparece na tela, a frase da narração e o texto de destaque.
3. Mostre o roteiro ao Patrick em 5 linhas e siga em frente se ele não pedir mudança.

## Etapa 3: Gravar as cenas (Movie Maker do Godot)
1. Copie `trailer/godot/camera_trailer.gd` (deste kit) para `res://trailer/camera_trailer.gd`.
2. Monte `res://trailer/trailer.tscn`: instancie a cena do mapa da fazenda, o personagem e os
   elementos da atualização. Adicione um `Camera2D` com o script e um `Marker2D` filho por tomada,
   com os metadados `zoom`, `duracao`, `transicao` e `deriva` (explicados no topo do script).
   - Desligue a câmera do jogador na cena de trailer e esconda a interface (HUD) quando não for o foco.
   - Dê vida às tomadas: personagem andando, plantas crescendo, partículas leves (CPU), animais.
     Use `AnimationPlayer`/`Tween` para ações roteirizadas em vez de depender de input.
3. Grave sem janela travando (o Movie Maker renderiza quadro a quadro, então roda perfeito neste PC):
   ```powershell
   & $env:GODOT_BIN --path . --write-movie trailer/gravacoes/trailer.avi --fixed-fps 60 --resolution 1920x1080 res://trailer/trailer.tscn
   ```
   O script fecha o jogo sozinho no fim. Para pixel art nítida, use stretch mode `viewport` e
   escala inteira; se a resolução nativa for pequena (ex.: 480x270), grave nela e amplie depois
   com `ffmpeg -vf scale=1920:1080:flags=neighbor`.
4. Para o vertical, grave uma segunda vez com `--resolution 1080x1920` e zoom maior, em vez de
   só cortar o horizontal.
5. Confira: extraia 1 quadro por tomada com FFmpeg e veja se está enquadrado e sem tela preta.

## Etapa 4: Narração (a parte que mais tira a cara de IA)
Escolha nesta ordem:
1. **Voz do próprio Patrick**, se houver `trailer/narracao/minha-voz.wav`: limpe ruído com o filtro
   `afftdn` + `highpass=f=80` + `loudnorm` do FFmpeg e use essa voz.
2. **Chatterbox Multilingual (MIT, pt-BR, controle de emoção)** pelo Space oficial da Resemble AI
   no Hugging Face, usando `gradio_client` (procure o Space oficial "Chatterbox Multilingual").
   Se precisar de token, peça ao Patrick para criar uma conta grátis em huggingface.co e salvar o token
   como variável `HF_TOKEN` (nunca no chat). `exaggeration` entre 0.5 e 0.7, `cfg_weight` ~0.4.
3. **Kokoro, local no processador** (padrão se as outras não estiverem disponíveis):
   `KPipeline(lang_code='p')`, vozes `pm_alex` (masculina) ou `pf_dora` (feminina), `speed` 1.05.
   Gere **uma frase por arquivo** e junte com 250 a 400 ms de silêncio entre elas: soa bem mais humano
   do que tudo de uma vez.
- Nunca use XTTS-v2, Fish Audio ou Voxtral: as licenças não permitem uso comercial.

## Etapa 5: Legendas com tempo de palavra
- Transcreva a narração final com `faster-whisper` (`WhisperModel("small", device="cpu",
  compute_type="int8")`, `language="pt"`, `word_timestamps=True`) e salve
  `trailer/narracao/legendas.json` (palavra, início, fim).
- Corrija a grafia pelo texto do roteiro (o roteiro manda; o Whisper só dá o tempo).

## Etapa 6: Música
- Use uma faixa de `trailer/musica/`. Se estiver vazia, baixe uma faixa aconchegante/acústica com
  licença livre para uso comercial (Pixabay Music) e anote título, autor e link em `trailer/musica/CREDITOS.txt`.
- Detecte as batidas (BPM) e alinhe as trocas de tomada a elas.

## Etapa 7: Montagem (OpenMontage + Remotion)
- No OpenMontage, use o pipeline de **trailer cinematográfico** com os **clipes locais** de
  `trailer/gravacoes/`, a narração, `legendas.json` e a música. Sem geração de imagem ou vídeo por IA.
- Estilo de legenda: palavra ativa em destaque (cor da marca do jogo), contorno escuro, leve escala
  de entrada; posição a ~70% da altura no vertical.
- Textos de destaque curtos e animados ("NOVO: SISTEMA DE REGAR"), no máximo 4 palavras.
- Transições: cortes secos na batida + no máximo 2 transições suaves no vídeo inteiro.
- Mixagem: música a -18 dB sob a narração (ducking), -10 dB sem narração; master em -14 LUFS.
- Exporte `saida/atualizacao-vertical.mp4` (1080x1920) e `saida/atualizacao-horizontal.mp4`
  (1920x1080), H.264, 30 ou 60 FPS.
- Se o OpenMontage falhar e não houver correção rápida, monte com Remotion direto
  (componentes `<OffthreadVideo>`, `<Audio>` e legendas próprias) e siga o mesmo estilo.

## Etapa 8: Revisão antes de entregar
- `ffprobe`: duração, resolução, áudio presente.
- Extraia quadros nos segundos 1, 5, 10 e no final; confira legenda legível e nada cortado.
- Confirme que as legendas batem com a fala (amostre 3 pontos).
- Entregue ao Patrick: caminho dos dois MP4, 3 linhas sobre o que mudou e o que dá para ajustar.
- **Nunca publique** em rede social sem ele aprovar.
