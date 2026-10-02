# Prompts para gerar o herói andando para os outros lados

Use **um prompt por vez**, nesta ordem: **frente → costas → lado esquerdo**.
Só passe para o próximo depois de aprovar o vídeo do anterior.

Onde colar: na conversa do Claude Code que já está ligada ao repositório **jogo**
(ou numa sessão nova do Claude Code com esse repositório), na branch
`claude/conversa-perdida-nuvem-26xpxi`.

---

## 1) FRENTE (andando para baixo, vindo em direção à câmera)

```
MISSÃO — HERÓI ANDANDO DE FRENTE (com esqueleto)

Contexto: o andar de LADO DIREITO do herói já está pronto e aprovado, feito com a técnica de
"esqueleto" a partir de uma única pose do turnaround. Está no repositório "jogo", branch
claude/conversa-perdida-nuvem-26xpxi, pasta heroi_preparado/:
- fonte/frente.png (pose de frente, fundo já removido, 590 px de altura) e fonte/turnaround.png
- ferramentas/rig_heroi.py e ferramentas/anim_lado.py (técnica usada no lado direito: separar
  corpo, braço e perna; perna em 2 partes com cinemática inversa; bota que gira; contorno
  refeito com espessura uniforme; redução 9x para 64 px com paleta fixa de 32 cores e contorno
  escuro), ferramentas/gifs.py, previa.py e video_lado.py
- revisao/lado/ = resultado aprovado (use como referência de qualidade, ritmo e tamanho)

O que fazer: aplique a MESMA técnica na vista de FRENTE, criando ferramentas/anim_frente.py
(pode reaproveitar funções do anim_lado.py, sem mudar o resultado do lado direito).
1. Separe da pose de frente: corpo (cabeça + tronco + cintura), os dois braços e as duas pernas.
   As partes escondidas (entre as pernas, tronco atrás dos braços) devem ser completadas.
2. Pernas: alternam. A perna que dá o passo dobra o joelho, fica mais curta e o pé sobe 2–3 px
   e desce um pouco na tela (vindo para a câmera). A perna de apoio fica esticada no chão.
   Os pés não podem atravessar um ao outro.
3. Braços: balançam ao contrário das pernas. O braço que vai para a frente desce um pouco e a mão
   aparece um pouco maior/mais para fora; o que vai para trás sobe e a mão fica parcialmente
   escondida atrás do quadril. Movimento pequeno (1–2 px no tamanho do jogo).
4. Corpo: sobe e desce 1–2 px (mesmo ritmo do lado: 1, 2, 1, 0 px) e pode balançar no máximo 1 px
   para o lado da perna de apoio. A cabeça não entorta.
5. Regras que já foram corrigidas no lado e valem aqui também:
   - o tronco nunca pode ganhar "corcunda"/volume estranho quando o braço se mexe: o espaço que
     o braço deixa é preenchido só até o contorno real do tronco;
   - a bota fica SEMPRE encaixada na calça (a barra da calça acompanha o ângulo da bota, sem vão).
6. Mesmo padrão do lado: 8 quadros + 1 parado, 75 ms por quadro, mesma escala (9x → 64 px),
   mesma paleta/contorno, pivô no meio dos pés, sem borrar, sem esticar, sem mudar o tamanho.
7. Entregue em revisao/frente/: parado.png, andar_0..7.png, info.json, prancha_final.png,
   um GIF ampliado e um vídeo MP4 (andando no gramado + câmera lenta), como no lado.
8. Faça commit e push na mesma branch e me mande o vídeo e a prancha para eu aprovar.
   Se algo não ficar natural, me diga com sinceridade antes de seguir.
```

---

## 2) COSTAS (andando para cima, indo embora da câmera)

```
MISSÃO — HERÓI ANDANDO DE COSTAS (com esqueleto)

Contexto: os andares de LADO DIREITO e de FRENTE do herói já estão prontos e aprovados, feitos com
a técnica de "esqueleto". Repositório "jogo", branch claude/conversa-perdida-nuvem-26xpxi, pasta
heroi_preparado/:
- fonte/costas.png (pose de costas, fundo já removido, 590 px de altura) e fonte/turnaround.png
- ferramentas/anim_lado.py e ferramentas/anim_frente.py (técnica aprovada)
- revisao/lado/ e revisao/frente/ = resultados aprovados (referência de qualidade e ritmo)

O que fazer: aplique a MESMA técnica da FRENTE na vista de COSTAS, criando
ferramentas/anim_costas.py (sem mudar os resultados já aprovados).
1. Separe da pose de costas: corpo (cabeça/chapéu + tronco + cintura), os dois braços e as duas
   pernas, completando as partes escondidas.
2. Pernas: alternam. A perna que dá o passo dobra o joelho, o pé sobe 2–3 px e vai um pouco para
   cima na tela (indo embora). Quando o pé sai do chão, dá para ver um pouco a sola da bota
   (mais escura). A perna de apoio fica esticada no chão.
3. Braços: balançam ao contrário das pernas. Visto de costas, a mão que vai para trás desce e
   aparece um pouco maior; a que vai para a frente sobe e fica parcialmente escondida pelo corpo.
   Movimento pequeno (1–2 px no tamanho do jogo).
4. Corpo: sobe e desce no mesmo ritmo da frente (1, 2, 1, 0 px), balanço lateral de no máximo
   1 px. O chapéu e a cabeça não entortam.
5. Regras que valem sempre: sem "corcunda"/volume estranho no tronco quando o braço se mexe;
   bota sempre encaixada na calça, sem vão.
6. Mesmo padrão: 8 quadros + 1 parado, 75 ms, escala 9x → 64 px, mesma paleta e contorno, pivô no
   meio dos pés, sem borrar, sem esticar, sem mudar o tamanho. O ritmo deve casar com o da frente.
7. Entregue em revisao/costas/: parado.png, andar_0..7.png, info.json, prancha_final.png,
   GIF ampliado e vídeo MP4 (andando no gramado + câmera lenta).
8. Faça commit e push na mesma branch e me mande o vídeo e a prancha para eu aprovar.
   Se algo não ficar natural, me diga com sinceridade antes de seguir.
```

---

## 3) LADO ESQUERDO (andando para a esquerda)

```
MISSÃO — HERÓI ANDANDO PARA A ESQUERDA (com esqueleto, SEM espelhar)

Contexto: os andares de LADO DIREITO, FRENTE e COSTAS do herói já estão prontos e aprovados.
Repositório "jogo", branch claude/conversa-perdida-nuvem-26xpxi, pasta heroi_preparado/:
- fonte/lado_esq.png (pose de lado esquerdo DESENHADA, fundo já removido, 590 px de altura)
- ferramentas/rig_heroi.py e ferramentas/anim_lado.py (técnica aprovada do lado direito)
- revisao/lado/ = andar do lado direito aprovado

O que fazer: refaça a técnica do lado direito usando a pose DESENHADA do lado esquerdo, criando
ferramentas/rig_heroi_esq.py e ferramentas/anim_lado_esq.py (sem mudar o lado direito).
1. NÃO espelhe o lado direito: a luz, o braço que aparece e os detalhes são outros. Meça de novo,
   na pose do lado esquerdo, o quadril, joelho, tornozelo, ombro, cotovelo, a separação das
   pernas e o braço que aparece.
2. Tudo que era "para a frente" agora é para a ESQUERDA: o joelho dobra para a esquerda, a ponta
   da bota aponta para a esquerda e o giro da bota (calcanhar no contato, ponta do pé no impulso)
   fica invertido.
3. Mesmo ciclo do lado direito: mesmas posições dos pés (espelhadas só nos números), mesmo sobe e
   desce (1, 2, 1, 0 px), mesmo balanço dos braços, mesma velocidade (pés sem escorregar).
4. Regras que valem sempre: costas retas quando o braço vai para a frente (sem corcunda); bota
   sempre encaixada na calça, sem vão; perna e braço de longe mais escuros e escondidos quando
   devem ficar atrás do corpo.
5. Mesmo padrão: 8 quadros + 1 parado, 75 ms, escala 9x → 64 px, mesma paleta e contorno, pivô no
   meio dos pés, mesma altura do lado direito.
6. Confira: coloque o andar da esquerda ao lado do da direita (espelhado só para comparar) e veja
   se ritmo, altura e tamanho batem.
7. Entregue em revisao/lado_esq/: parado.png, andar_0..7.png, info.json, prancha_final.png,
   GIF ampliado e vídeo MP4 (andando no gramado + câmera lenta).
8. Faça commit e push na mesma branch e me mande o vídeo e a prancha para eu aprovar.
   Se algo não ficar natural, me diga com sinceridade antes de seguir.
```
