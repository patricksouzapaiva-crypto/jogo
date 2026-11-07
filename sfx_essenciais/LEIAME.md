# Efeitos sonoros essenciais — Raízes da Memória

Pacote **essencial** gerado no ElevenLabs (Sound Effects v3) a partir do
`PEDIDO_EFEITOS_SONOROS_ELEVENLABS.md`. Por decisão do projeto, foram produzidos só os
sons mais importantes; reservas (P), caderno, transições, neve, criaturas, máquinas
específicas (tear, prensa, queijeira, mel) e loops de culinária ficaram de fora.

**60 famílias · 135 arquivos** (128 pontuais + 7 ambientes em loop).

## Pastas
| Pasta | Conteúdo |
|---|---|
| `audio/sfx/<chave>_<n>.ogg` | Arquivos prontos para o jogo (OGG Vorbis, 48 kHz, índices a partir de 0) |
| `masters_trabalho/` | WAV 48 kHz tratados (recorte, microfades, mono, nível por família, pico ≤ -3 dBTP) |
| `masters_originais/` | WAV 48 kHz exatamente como saíram do ElevenLabs (16 bits — a fonte não oferece 24) |
| `previas/` | Só para ouvir: todos os pontuais em sequência e cada ambiente tocado 2× seguidas (para conferir a emenda) |
| `manifesto.csv` | Chave, variação, duração, categoria, mono/estéreo, loop/pontual, pico, observações, origem, prompt e notas da revisão |

## Como foi feito
1. Prompt-base do pedido (calmo, orgânico, sem música/voz) + descrição de cada linha, em inglês (o modelo entende melhor).
2. Uma variação extra por família; todas as candidatas foram **ouvidas pelo Gemini** e avaliadas
   (fidelidade 0–10, calma 0–10, presença de voz/música). Só entraram as com nota ≥ 6 nas duas, sem voz.
   Ex. de descartes: "galinha" que soava como risada humana, "foice" e "linha de pesca" que soavam como tosse/respiração.
3. Pontuais: mono, silêncio inicial removido, cauda natural preservada, microfades; variações de uma mesma
   família igualadas por volume percebido; **famílias não foram igualadas entre si** (equilibrar no jogo).
4. Galo: o modelo só gerava galo próximo; a distância foi simulada em pós (passa-baixa, eco curto, -14 dB).
5. Ambientes: estéreo, 20 s, emenda por crossfade de 2 s; salto na emenda medido e aprovado em todos.

## Limitações
- A revisão automática não substitui ouvir no jogo: seguir os critérios de aprovação do pedido
  (repetir 30×, volume baixo, mono, sessão de 10–15 min, sobreposição com música).
- `plantar` ficou com 2 variações (pedido: 3) e `animal_galo` com 2 — as demais candidatas foram reprovadas.
- Ambientes com 1 loop cada (o pedido sugere 2–3); dá para gerar mais depois.
- Produção ≠ integração: as chaves novas (N) precisam ser ligadas no código.
