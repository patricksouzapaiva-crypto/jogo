# Prompt para o chat principal (integração no projeto)

Copie a pasta `fauna_preparada/` para dentro da pasta do projeto, ao lado de `JogoFazenda/`, e cole o texto abaixo no chat principal.

```
Preparei fora do projeto as animações da fauna (Penala, pato anfíbio, ovelha,
Gruntho e vaca) a partir do MOVIMENTACOES_DOS_ANIMAIS_v1. Está tudo em
fauna_preparada/. Leia primeiro fauna_preparada/LEIA_PRIMEIRO_FAUNA.md.

1. INSPECIONE O PROJETO (nada foi feito aqui ainda)
- Identifique o sistema atual de animação dos animais, a escala, a câmera,
  os pivots, a importação e a movimentação.
- Faça backup dos animais atuais para comparação e rollback.
- Não crie um sistema paralelo sem necessidade: adapte à arquitetura que
  já existe. O carregador_fauna.gd é opcional e pode servir de base.

2. COPIE SEM SUBSTITUIR
- Copie fauna_preparada/JogoFazenda/arte/preparado/fauna/ e
  fauna_preparada/JogoFazenda/testes/fauna/ para as mesmas pastas do projeto.
- Confira a importação dos atlas: Nearest, sem mipmaps, compressão Lossless.
- Rode a verificação:
  godot --headless --path . --script res://testes/fauna/verificar_fauna.gd
  (fora do projeto deu PASSOU, 116 de 116).

3. CONFIRA A ESCALA
- Compare os tamanhos propostos (tabela da seção 2 do relatório) com o
  protagonista e com os animais que já estão no jogo. Se precisar mudar,
  edite fauna_preparada/ferramentas/escala_especies.json e rode
  fauna_preparada/ferramentas/rodar_tudo.py. Não estique os atlas.

4. TESTE NA CENA DE TESTE E NO TERRENO REAL
- Coloque a textura do chão do jogo em textura_terreno.
- Ajuste a velocidade de deslocamento de cada espécie com "Chão andando"
  até os pés escorregarem o mínimo possível. Grave os valores.

5. INTEGRE AOS ANIMAIS DO JOGO, SÓ DEPOIS DA MINHA APROVAÇÃO
- Use pivot no chão (centered=false, offset=-pivot) e as durações do JSON.
- Não reinicie a animação a cada atualização.
- Respirar/piscar com pausa aleatória. Ações em intervalos variados.
  Não altere necessidades, produção nem outras regras do jogo.
- Não implemente sono, repouso nem nado (não estão no pacote).

6. ME TRAGA AS DECISÕES PENDENTES (seção 5 do relatório)
- Ações para a esquerda: espelhar ou desenhar?
- Parado de frente e de costas: segurar o 1º quadro da caminhada por enquanto?
- Os 3 redesenhos (vaca de lado, vaca para cima, Gruntho para cima): prepare
  um pedido para a IA de arte com animal, animação, direção, quadros e o que
  corrigir, anexando as folhas originais como referência.

Explique tudo em linguagem simples.
```
