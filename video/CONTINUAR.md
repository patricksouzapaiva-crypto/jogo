# Para continuar numa sessão nova

Leia antes de qualquer coisa: `video/GUIA_DO_EDITOR.md` (regras da casa, seções 11 e 12) e
`video/ESTUDO_CANAIS_TERROR.md`. O motor está em `video/painel/` (`gerar.py`, `pagina/motor.js`, `render.js`).

## Estado em 09/11/2026
- **Ep. 01 "O Retrovisor"** (Short) e **Ep. 02 "A Sonâmbula"** (longo + 3 Shorts): prontos e entregues.
- **Ep. 03 "Mais perto."** (11min52): **aprovado** (v4, teclado mecânico). Publicação em
  `episodios/ep03-conceito/publicacao/YOUTUBE.md` + `legendas_pt-BR.srt`.
  Renderizar de novo: `python3 video/painel/gerar.py video/episodios/ep03-conceito/roteiro.json saida.mp4`
  (a narração `audio/voz_completa_v2.wav` não vai pro git — se faltar, pedir ao usuário ou regravar).
- **Imagens reais:** modelo híbrido aprovado (seção 12 do guia). `PIXABAY_API_KEY` foi cadastrada nas
  variáveis de ambiente pelo usuário — testar logo no começo:
  `python3 video/painel/ferramentas/buscar_imagens.py buscar /tmp/t consultas.json`.

## Pendências
1. Testar Pixabay (variável `PIXABAY_API_KEY`).
2. **3 Shorts do Ep. 03** ("A mensagem", "Encontre a criatura", "O microfone") — ver `publicacao/YOUTUBE.md`;
   Vigia HD, CTA com `cenarios/abrigo_vertical.png` e pose `c_cafe_convite` (modelo: `ep02-a-sonambula/montar_shorts.py`).
3. Estudo de **edição de som** no estilo Fyori: o YouTube bloqueia download aqui ("confirme que não é um robô");
   usar as gravações que o usuário enviar. Ideia: separar voz/fundo (demucs) e medir onde entram efeitos,
   silêncios e trilha em relação às palavras.
4. Músicas via KIE.AI/Suno (`painel/ferramentas/musica_kie.py`) — aguardando conta/chave do usuário.

## Regras que o usuário cobra sempre
Narração pelo Google Gemini TTS (grátis); ElevenLabs só para música/efeitos e pouco. Troca de pose só entre
palavras. Nada de chiado. Trilha presente mas nunca por cima da voz; silêncio como ferramenta. Não encurtar
as pausas da narração. Vigia em alta resolução, troca de lado às vezes. CTA no fim. Nunca pedir chave no chat.
