# Efeitos sonoros complementares — Raízes da Memória

Segunda leva, complementando `sfx_essenciais/`. Mesmo método, mesmo tratamento e mesma
nomenclatura (`audio/sfx/<chave>_<n>.ogg`). Pode juntar as duas pastas `audio/sfx/` no jogo: as chaves não se repetem.

**38 famílias · 97 arquivos** (84 pontuais + 13 ambientes em loop de 20 s).

| Grupo | Chaves |
|---|---|
| Caderno e transições | caderno_abrir, caderno_fechar, pagina_virar, escrita_curta, transicao_dia, transicao_estacao |
| Passos | passo_neve, agua_rasa_passo |
| Animais / pesca | sino, pesca_soltar, pesca_isca |
| Máquinas | queijeira_inicio, tear_inicio, prensa_inicio, mel_colher, abelhas_proximas (loop), tear_trabalho (loop), prensa_trabalho (loop) |
| Culinária (loops) | cozinha_fervura, cozinha_assar, cozinha_refogar |
| Casa | porta_vidro_abrir, porta_vidro_fechar, lareira (loop), estufa_ambiente (loop) |
| Cidade | caixa_correio, fonte_praca (loop), interior_biblioteca (loop), interior_taverna (loop) |
| Criaturas | criatura_curiosa, criatura_passo, habitat_colocar, habitat_cuidar, vestigio_descobrir, memoria_encontrada |
| Clima / estações | gota_folha, vento_inverno (loop), folhas_outono (loop) |

## Pendências
- **criatura_contente e criatura_sonolenta não foram geradas de propósito**: o pedido manda aprovar
  primeiro a voz de uma criatura. Ouça `criatura_curiosa_*`; se aprovada, gero as outras com o mesmo timbre.
- `prensa_inicio` ficou com 1 variação (pedido: 3) e `tear_inicio` com 2 — as demais candidatas foram reprovadas.
- Loops com 1 arquivo cada (pedido: 2); 20 s (pedido: 15–40 s).
- Revisão automática (Gemini) não substitui ouvir no jogo; integração no código continua necessária.
