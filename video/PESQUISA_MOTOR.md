# Pesquisa: como melhorar o motor de vídeo (16/11/2026)

O que foi comparado: motores de vídeo por código (Remotion, Motion Canvas, Revideo), linhas de montagem automáticas
(MoneyPrinterTurbo, MoneyPrinter, ShortGPT), alinhamento de fala (WhisperX, stable-ts), câmera 3D a partir de foto
(3D Ken Burns, 3D Photo Inpainting, DepthFlow, Video Depth Anything), interpolação de quadros (RIFE), cor de cinema
(LUT, grão, halação) e mixagem (sidechain, loudnorm). Comparação com o nosso motor medido nos renders do Ep. 10.

## Onde o nosso motor está
- **Render:** Chromium headless + canvas 2D, 4 processos (a máquina tem 4 núcleos), quadro → JPEG (`toDataURL`) →
  ffmpeg. Final 1080p de 15 min: 26.821 quadros em 2.293 s (11,7 quadros/s); rascunho: 892 s.
- **Tempo das palavras:** faster-whisper (tempos aproximados) + casamento com o roteiro + ajuste pelo silêncio real.
  Foi a origem dos erros de "palavra presa na legenda" e de pausa cortando a 1ª palavra (corrigidos por regra).
- **Câmera 3D:** Depth Anything V2 Small + deformação da imagem (`remap`), bordas por reflexo, **sem preencher** o
  que aparece atrás dos objetos.
- **Revisão:** `revisar.py` (voz, roteiro, folhas de cena, silêncio, desaceleração, mix) — agora também **varre
  piscadas** no vídeo inteiro (16/11).

## O que os outros fazem melhor e vale trazer (por prioridade)

| # | Melhoria | De onde vem | Ganho | Custo |
|---|---|---|---|---|
| 1 | **Alinhamento forçado ao TEXTO do roteiro** (modelo de fonemas wav2vec2/CTC, ~50–100 ms) no lugar do Whisper+casamento | WhisperX, stable-ts | legenda e cortes exatos, fim dos erros de palavra trocada/atrasada; vozes de personagem alinhadas mesmo quando o TTS troca "tá"/"está" | médio (modelo PT ~360 MB–1,2 GB; disco curto) |
| 2 | **Revisão automática de transições de áudio** (Whisper nos 6 s em volta de cada fala de personagem: a narração seguinte começa inteira?) | aprendido no Ep. 10 | pega sozinho o erro que o usuário achou no rascunho 1 | baixo |
| 3 | **Câmera 3D com preenchimento** (camadas de profundidade + inpainting das áreas reveladas; ou shader estilo DepthFlow) | 3D Photo Inpainting, DepthFlow | movimento maior sem "esticar" bordas; mais parecido com câmera de verdade | médio |
| 4 | **"Look" de cinema no final** (LUT .cube por episódio via `lut3d` + halação/bloom leve + grão por quadro) | color-fx, Dehancer (ideia) | cor consistente entre imagens de IA, fotos reais e trailers | baixo |
| 5 | **Ducking por sidechain** só como verificação do nosso `automixar` + loudnorm em 2 passadas na entrega | ffmpeg cookbook | mix mais estável, sem "aviso salto" | baixo |
| 6 | **Render mais rápido**: medir `quadro()` × `toDataURL`; testar captura por `HeadlessExperimental.beginFrame` / sem base64 (buffer binário) e JPEG 0,9 | puppeteer-capture, fórum Chromium | 20–40 % menos tempo (a medir) | médio |
| 7 | **Interpolação RIFE** (CPU, ncnn) para os trechos de arquivo e câmera lenta, no lugar do `minterpolate` | RIFE | câmera lenta sem "borrão de fusão" | médio-alto (CPU lento) |
| 8 | **Profundidade consistente em clipes** (Video Depth Anything) para aplicar parallax/neblina em vídeo | Video Depth Anything | efeitos 3D em clipes do Flow sem tremer | alto |

**Não vale trocar de motor.** Remotion (licença paga para empresas, DOM), Motion Canvas/Revideo (MIT, canvas como o
nosso) e MoneyPrinterTurbo (MoviePy, banco de imagens genérico) fariam menos do que o nosso já faz: chat animado,
câmera de segurança, cartões 3D, Vigia com poses, legendas palavra a palavra, mix automático. O ganho está em
trazer as PEÇAS acima para dentro do motor atual.

## Ordem proposta
1. (feito) piscadas no `revisar.py`.
2. Revisão das transições personagem → narração no `revisar.py` (item 2).
3. Look de cinema configurável no roteiro (`"look": {"lut": "...", "halacao": 0.2}`) aplicado no encode final (item 4).
4. Alinhamento forçado ao texto (item 1) — testar num episódio antigo e comparar as legendas.
5. Câmera 3D com preenchimento (item 3) — prévia lado a lado com a atual para o usuário escolher.
6. Medir e acelerar o render (item 6).

## Fontes
- Remotion × Motion Canvas × Revideo: https://www.pkgpulse.com/guides/remotion-vs-motion-canvas-vs-revideo-programmatic-video-2026 ·
  https://www.remotion.dev/docs/compare/motion-canvas
- MoneyPrinterTurbo (arquitetura): https://agentpedia.codes/blog/moneyprinterturbo-ai-short-video-generator-guide
- WhisperX (artigo): https://arxiv.org/abs/2303.00747
- 3D Ken Burns: https://github.com/n1ckfg/3d-ken-burns · 3D Photo Inpainting: https://github.com/duyamin/3d-photo-inpainting
- DepthFlow: https://pypi.org/project/depthflow/
- Video Depth Anything: https://arxiv.org/abs/2501.12375v1
- RIFE (ncnn): https://github.com/TNTwise/rife-ncnn-vulkan
- Ducking no ffmpeg: https://ffmpeg-cookbook.pages.dev/en/articles/audio-ducking/
- color-fx (LUT, grão, halação): https://pypi.org/project/color-fx/
- Captura determinística no Chromium: https://socket.dev/npm/package/puppeteer-capture
