# Motor "avatar + painel animado"

Gera vídeos 9:16 no estilo da referência `video/referencias/estilo-avatar-painel.md`:
título cinético, painel que se monta a cada frase, avatar com poses e áudio mixado.

```bash
pip install faster-whisper opencv-python-headless numpy requests   # + ffmpeg, node 22 e playwright
python video/painel/gerar.py video/painel/exemplos/flannan/roteiro.json saida.mp4 [--rascunho]
```

| Etapa | Ferramenta | Custo |
|---|---|---|
| Narração | Google Gemini TTS (`gemini-2.5-flash-preview-tts`) | grátis |
| Tempo de cada palavra | Whisper local (`faster-whisper`, modelo small) | grátis |
| Pausas longas | encurtadas automaticamente (ponto 0,42 s · vírgula 0,24 s) | — |
| Quadros | Chromium headless + `pagina/motor.js`, 4 em paralelo (~1 s de render por s de vídeo) | grátis |
| Trilha e efeitos | `sons/` (gerados uma vez no ElevenLabs e reaproveitados) | já pago |
| Volume final | −14 LUFS, pico ≤ −1 dBTP | — |

## Roteiro (JSON)

```jsonc
{
  "tema": "vigia",            // temas/<nome>.json (cores e fontes)
  "avatar": "vigia",          // avatares/<nome>/ (poses + poses.json)
  "assinatura": "o vigia / casos",
  "barra": "MEDO",            // barra que enche ao longo do vídeo (opcional)
  "voz": {"modelo": "...", "nome": "Charon", "estilo": "Narre em português do Brasil, ..."},
  "trilha": {"ambiente": "ambiente_terror", "volume_db": -17},
  "batidas": [
    {"fala": "Três homens. Uma ilha. Nenhum corpo.",
     "titulo": ["TRÊS", "HOMENS"],                       // linha 1 branca, linha 2 na caixa
     "titulos": [{"em": "Uma", "linhas": ["UMA", "ILHA"]}], // troca de título presa a uma palavra
     "pose": "sussurrando", "poses": [{"em": "Nenhum", "pose": "encarando_a_camera"}],
     "painel": {"tipo": "lista", "etiqueta": "O QUE SOBROU?", "itens": [
        {"texto": "0 CORPOS", "icone": "caveira", "em": "Nenhum", "riscar": "corpo"}]}}
  ]
}
```

- `"em": "palavra"` prende a animação ao instante em que a voz diz essa palavra (dentro da batida).
- Batida sem `painel` mantém o anterior; `"painel": null` tira; `"continua": true` acrescenta ao painel atual.
- **Painéis:** `lista` (itens com ícone, `riscar`), `checklist` (papel; `marca` "x"/"ok", `marcar`,
  `risca_texto`), `ficha` (dossiê; `campos`, `imagem`, `carimbo`), `contador` (`de`, `ate`,
  `em_contagem`, `nota`), `chat` (`mensagens` de "eu"/"ele"), `impacto` (`pequeno`, `grande`,
  `em_grande`), `imagem` (cena ilustrada com movimento lento, `legenda`).
- **Ícones:** olho, lua, vela, chave, porta, relogio, alerta, casa, livro, farol, barco, pessoa,
  camera, capa, caveira, ondas, interrogacao.
- **Poses do Vigia:** nomes dos arquivos em `avatares/vigia/` (ex.: `neutro`, `sussurrando`,
  `assustado`, `pensativo`, `apontando_para_publico`, `sorriso_sinistro`, `oculto_nas_sombras`).
- Efeitos sonoros automáticos: whoosh na entrada de painel, tecla em cada item, impacto em
  carimbo e frase de impacto.

Novo avatar: `python video/painel/ferramentas/preparar_avatar.py <pasta_pngs> video/painel/avatares/<nome>`.
