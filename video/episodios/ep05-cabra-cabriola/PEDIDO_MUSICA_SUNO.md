# Ep. 05 — música de fundo no Suno

A trilha toca o episódio inteiro, baixa, embaixo da narração. Por isso: **sem bateria, sem pancadas, sem sustos,
volume constante, sem letra**. Marque **Instrumental** no Suno. Gere 2–4 versões de cada e me mande todas (mp3 ou
wav); eu escolho, emendo e deixo no tamanho do episódio.

## Trilha A — fundo principal (a casa de madrugada)
**Style of Music:**
```
dark ambient horror underscore, slow 50 bpm, D minor, low bowed cello and contrabass drone, sparse felt piano single notes with long silence between them, distant detuned music box lullaby, faint wordless female humming far away slightly out of tune, deep room reverb, old house at night, tape hiss free, warm low end, no drums, no percussion, no sudden hits, no jump scares, no risers, steady quiet dynamics, cinematic, unsettling, patient, minimal
```
**Título:** `Abre, filha — fundo`

## Trilha B — tensão (as noites em que a voz volta e o clímax)
**Style of Music:**
```
tense horror drone underscore, 45 bpm, D minor with minor second clusters, sustained low strings slowly swelling and fading, bowed metal and distant anvil resonance far in the background, sub bass pulse like a slow heartbeat very soft, high glassy violin harmonics, breathing texture, claustrophobic, something waiting behind a door, no drums, no percussion hits, no melody, no vocals, no sudden loud sounds, no jump scares, gradual and continuous, dark cinematic ambient
```
**Título:** `Abre, filha — tensão`

## Trilha C (opcional) — a cantiga da mãe (epílogo / tema)
**Style of Music:**
```
lonely Brazilian lullaby melody hummed by a tired woman, wordless, slow and soft, accompanied only by a faint old music box and a low cello drone, melancholic, intimate, slightly eerie, D minor, lots of reverb, no drums, no lyrics, no sudden changes
```
**Título:** `Abre, filha — cantiga`

## Se o Suno pedir "Lyrics" mesmo no instrumental
Cole só isto (são marcações de estrutura, não letra):
```
[Intro: low drone, very quiet]
[Instrumental: slow, sparse, no drums]
[Instrumental: continues, same intensity]
[Outro: fade out slowly]
```

## Dicas
- Duração: quanto maior, melhor (use **Extend** até 4–8 min). Eu faço o laço sem emenda aparente.
- Se vier com bateria, batida forte ou voz cantando palavras: gere de novo acrescentando no fim do estilo
  `strictly no drums, strictly instrumental`.
- Baixe em **WAV** se o plano permitir (senão MP3).

---
## Resultado da 1ª leva (10/11) e pedido de nova versão
Recebidas 6 faixas (`musica/suno_*.mp3`). Medição:
- A1/A2 (fundo, ~60 s) e B1/B2 (tensão, 40–50 s): **87–96% da energia abaixo de 250 Hz** → no alto-falante do
  celular quase não se ouve (mesmo problema do Ep. 04) e são curtas demais para 15 min sem repetir.
- C1/C2 (cantiga, 2min33 e 2min58): na faixa média, dá pra ouvir bem; C2 é a mais regular (C1 tem um salto de
  +18 dB aos 33 s). Boas para o tema e o epílogo; baixas, porque ficam na mesma faixa da voz.

**Trilha A v2 (fundo que se ouve no celular):**
```
dark ambient horror underscore, slow 50 bpm, D minor, mid-register cello and viola sustained notes, sparse felt piano single notes in the middle register with long silence between them, distant detuned music box lullaby, soft high string harmonics, audible on small phone speakers, clear midrange, very little sub bass, deep room reverb, old house at night, no drums, no percussion, no sudden hits, no jump scares, no risers, steady quiet dynamics, unsettling, patient, minimal, strictly instrumental
```
**Trilha B v2 (tensão):**
```
tense horror underscore, 45 bpm, D minor with minor second clusters, sustained mid and high strings slowly swelling and fading, bowed metal and distant anvil resonance far in the background, glassy violin harmonics, quiet tremolo violas, clear midrange audible on phone speakers, very little sub bass, claustrophobic, something waiting behind a door, no drums, no percussion hits, no vocals, no sudden loud sounds, no jump scares, gradual and continuous, strictly instrumental
```
Usar **Extend** até passar de 4 minutos em cada.

---
## Decisão final da música (10/11/2026)
- O usuário rejeitou as faixas do Suno consertadas ("muito metálico") e a 1ª composição em código ("muito normal").
  **Aprovou o `musica/exemplos/exemplo3_sinistro.mp3`** = `painel/ferramentas/sintetizar_piano_violino.py`
  (`fundo2` e `tensao2`): piano velho desafinado, notas ao contrário, nuvens de violinos, glissandos, trítono.
  Arquivos do episódio: `painel/sons/ep05_fundo_longa.mp3` (16 min), `ep05_tensao_longa.mp3` (8 min).
- **Cantiga (`painel/sons/ep05_cantiga.mp3`, do Suno C2, levemente distorcida): entra SOZINHA** — o fundo sai antes.
- **Músicas prontas "livres" NÃO entram.** Verificado em 10/11: as de Kevin MacLeod são de fato CC BY 4.0, mas o
  próprio site dele avisa que terceiros registram as faixas no Content ID e geram reivindicações falsas
  (https://incompetech.com/music/royalty-free/youtube-contentid.html). A nossa trilha é composta em código por nós:
  não existe em nenhum banco de Content ID. As referências baixadas para estudo foram apagadas do repositório.
