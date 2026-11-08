# Pedido para o ChatGPT — O Vigia em alta resolução (meio corpo)

**Por quê:** hoje cada pose tem só ~320 px de altura (rosto ~100 px). No vídeo o rosto aparece com
~150 px no canto e ~300 px quando o Vigia fica em destaque → ampliação de 1,5× a 3× = borrado em
tela grande. **Regra nova:** gerar grande (rosto com 350–450 px) e o motor reduz quando precisar —
reduzir não perde qualidade, ampliar sempre perde.

## Como pedir
- **Uma pose por imagem**, retrato **1024×1536**, fundo **transparente** (PNG).
  Se o fundo transparente falhar, peça fundo **cinza liso #808080** (eu recorto).
- **Mesmo enquadramento em todas:** da cintura para cima, personagem centralizado, o topo do
  cabelo a ~6% do topo da imagem, a base corta na cintura. Mãos e cabelo **sem encostar na borda**.
- Comece pelas **12 mais usadas** (marcadas com ★); o resto pode vir depois.
- Anexe a prancha atual (meio corpo) como referência de rosto, roupa e cores em todo pedido.

## Bloco base (colar primeiro na conversa)
```
I will ask for single-pose images of the same character. Rules for EVERY image:
- One pose per image, portrait 1024x1536, transparent background (PNG). No scenery, no text.
- Character: "O VIGIA", the narrator from the attached sheet — young man, dark curly hair, pale skin, thin face, dark brown long coat with high collar, black turtleneck, small crescent-moon golden brooch on the left side of the coat. Keep face, hair, coat and colors IDENTICAL to the reference.
- Framing identical in all images: waist-up, centered, top of the hair at about 6% from the top edge, the bottom edge cuts at the waist; hands and hair never touch the image borders.
- Style: same semi-realistic illustrated style as the reference, sharp details, clean edges, soft cinematic lighting from the upper left, highly detailed face and eyes.
```

## Poses (um pedido por linha: "Pose: …")
**Conversa (prancha A)**
1. ★ c_falando — talking calmly to the viewer, mouth slightly open, neutral friendly face.
2. ★ c_dedo_explicando — raising the index finger at chest height as if making a point.
3. ★ c_desconfiado_lado — eyes looking to the side, slightly suspicious, mouth closed.
4. ★ c_serio_frontal — serious, looking straight at the viewer, hands down.
5. ★ c_preocupado — worried eyebrows, slightly tilted head.
6. ★ c_falando_olhar_lado — talking while glancing to the side.
7. ★ c_dar_de_ombros — light shrug, both palms open at hip height.
8. ★ c_olhar_cima — looking up, thoughtful, talking.
9. ★ c_mao_aberta_lado — one open hand extended to the side, presenting.
10. ★ c_oferecendo — one hand extended toward the viewer, palm up, inviting.
11. ★ c_pensativo_queixo — hand on chin, other arm crossed, thinking.
12. ★ c_cabisbaixo — head slightly down, eyes looking down, sad.
13. c_mao_no_peito — hand on chest, sincere.
14. c_sussurrando — hand beside the mouth as if telling a secret.

**Ênfase (prancha B)**
15. e_maos_na_boca — both hands over the mouth, eyes wide in shock.
16. e_pare — one hand pushed toward the viewer, palm out, alarmed.
17. e_aterrorizado_maos — terrified, hands raised and trembling near the face.
18. e_apontando — pointing straight at the viewer, intense stare.
19. e_bracos_cruzados_cetico — arms crossed, skeptical raised eyebrow.
20. e_medo_gola — gripping the coat collar with both hands, scared.

**Sombrio (prancha C)**
21. s_convidando — sly smile, one hand gesturing "come closer".
22. s_encarando — cold stare straight at the viewer, no smile.
23. s_sorriso_sombrio — slow sinister half-smile, eyes half-closed.
24. s_silencio — index finger over the lips ("shh"), serious eyes.

Salve com o nome da pose (ex.: `c_falando.png`) e me envie num .zip ou numa mensagem só com as imagens.
