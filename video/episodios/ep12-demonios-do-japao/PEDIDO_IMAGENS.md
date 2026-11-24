# Ep. 12: ilustrações que faltam, no ESTILO DAS GRAVURAS ANTIGAS (v2, 24/11)

**Pedido do usuário (24/11):** "as imagens poderiam ter o aspecto antigo, como se fossem essas imagens reais que você
achou, pra manter a identidade".

Todo o episódio é feito de gravuras e rolos reais, e estas ilustrações seguem o mesmo visual:
- **xilogravura ukiyo-e** (Yoshitoshi, Kuniyoshi, Sekien): traço de tinta preta, cores chapadas e desbotadas;
- impressas em **papel washi amarelado**, com fibras, manchas e bordas gastas.

A história da Camila acontece hoje, mas também é desenhada assim: uma fábrica, um celular e uma lanterna desenhados
como uma gravura do século XIX. Esse anacronismo é a graça.

**Regras:**
- **Nenhum rosto.** A Camila aparece só de costas, em silhueta ou só as mãos; a pessoa do ritual nunca mostra o rosto.
- **Sem texto, kanji, assinatura ou carimbo de artista** na imagem. Eu ponho o kanji na tela; um carimbo falso faria
  a ilustração parecer uma obra original. Na tela, elas não levam crédito de museu.
- **16:9.** Nome do arquivo = o código. Pasta `imagens/`.
- O `montar_roteiro.py` troca a reserva pela ilustração sozinho.

> **Padrões, idênticos em todos os prompts:**
> - **Camila:** `a young woman with long dark hair tied in a low ponytail, wearing a plain grey work jacket, seen only from behind or in silhouette`
> - **A pessoa do ritual:** `a figure in a long plain white kimono with an iron ring crown on the head holding three lit candles, long loose black hair, seen only from behind or in silhouette, face never visible`
> - **Estilo, no fim de TODOS:** `Edo-period Japanese ukiyo-e woodblock print in the style of Tsukioka Yoshitoshi and Toriyama Sekien, bold black ink outlines, flat faded colors (indigo, vermilion, ochre, grey), printed on aged yellowed washi paper with visible fibers, stains and worn edges, dark and eerie mood, 16:9, no faces visible, no text, no calligraphy, no signature, no seal stamp, no watermark`

## GANCHO: Matsudo, maio de 2022

| Código | Fala | Prompt |
|---|---|---|
| G01_arvore_santuario_madrugada | "os sacerdotes começaram a achar…" | `A huge ancient sacred cedar tree wrapped with a thick shimenawa straw rope and white paper zigzags at a small Shinto shrine at dawn, stone lanterns and mist, two shrine priests in white seen from behind looking up at the tree, + estilo` |
| G02_boneco_prego_tronco | "Bonecos de palha. Pregados…" | `Close view of a small crude straw doll nailed to the bark of a sacred tree with a long iron nail through its chest, a folded paper tied to it, more straw dolls nailed higher on other trees in the background, + estilo` |
| G03_camera_santuario | "A câmera de um santuário filmou…" | `A dark shrine grounds at night seen from high above at an odd angle, a stone path and a big tree, a small old man in dark clothes at the tree raising a hammer, seen from behind, very dark indigo night, + estilo` |

## A HISTÓRIA: a sétima noite

| Código | Fala | Prompt |
|---|---|---|
| H01_fabrica_noite | "Trabalha numa fábrica de autopeças, no turno da noite." | `A modern factory at night drawn as an Edo woodblock print, metal sheds, chimneys and glowing lamps, a few bicycles, Camila walking away toward the dark street, + estilo` |
| H02_bosque_santuario | "corta caminho pelo bosque de um santuário" | `A narrow stone path through the dark woods of a small neighborhood Shinto shrine at night, a weathered torii gate, tall cedar trunks, a single lamp post far behind, Camila small on the path seen from behind, + estilo` |
| H03_tres_chamas_arvores | "Três chamas. Paradas. Na altura de uma cabeça." | `Deep in dark shrine woods at night, three small candle flames floating side by side at the height of a person's head between the tree trunks, far away, nothing else visible, + estilo` |
| H04_tronco_escuro | "Metal batendo em madeira." | `The dark trunk of an old cedar lit by candlelight from the side, an iron hammer striking a long nail into the bark, only the hand in a white kimono sleeve visible, + estilo` |
| H05_rua_de_cima | "Volta pela rua de cima" | `An empty narrow Japanese residential street on a hill at night, wooden houses and a glowing vending machine drawn in woodblock style, Camila walking fast seen from behind, + estilo` |
| H06_boneco_foto | (a foto que chega no grupo do trabalho) | `A straw doll nailed to a sacred tree in pale morning light, a paper with handwriting tied to it (unreadable), shimenawa rope on the tree, + estilo` |
| H07_papel_data | "um papel com uma data de nascimento" | `Close view of a small folded paper tag tied with red string to a straw doll, a few unreadable ink brush marks on it, the nail just above, + estilo` |
| H08_celular_pesquisa | "A Camila pesquisa a noite inteira." | `A small dark Japanese room at night with a futon, a woman lying seen from behind holding a glowing smartphone, the screen a pale rectangle of light, drawn as an ukiyo-e print, + estilo` |
| H09_muro_noite | "Escondida atrás do muro" | `A low old stone wall at the edge of shrine woods at night, Camila crouching behind it seen from behind, dark trees beyond, + estilo` |
| H10_celular_na_mao | "com o celular na mão" | `Close view of a woman's hand holding a smartphone with the screen off in darkness, behind a mossy stone wall, + estilo` |
| H11_lanterna_feixe | "acendeu a lanterna do celular" | `A sharp white beam of light cutting through dark shrine woods toward a figure in a white kimono standing at a tree, seen from far behind the light, + padrão do ritual + estilo` |
| H12_coroa_velas_costas | "A pessoa virou devagar. As velas tremendo na cabeça." | `The figure in a white kimono seen from behind and above the shoulder, the iron crown with three trembling candles, long black hair, starting to turn, face not visible, + estilo` |
| H13_escuro | "conhecia aquele rosto" (o corte seco) | `Almost entirely black indigo woodblock print with only a thin curl of candle smoke rising, + estilo` |
| H14_martelo_no_chao | "Desceu o martelo." | `An old iron hammer hanging from a pale hand in a white kimono sleeve next to a cedar trunk, candlelight, no face, + estilo` |
| H15_chamas_apagando | "com as três chamas apagando uma por uma" | `Three small candle flames moving away deep into dark woods between tree trunks, one already out with a curl of smoke, + estilo` |
| H16_cadeira_vazia | "ela nunca mais viu" | `An empty work stool at a factory workbench at night with a pair of work gloves left on it, cold lamp light, drawn as an ukiyo-e print, + estilo` |
| H17_prego_novo | "E tinha um prego novo na árvore." | `A new shiny iron nail in the bark of the old sacred tree, next to many older rusty nail holes, grey morning, + estilo` |
| H18_papel_outra_data | "uma data de nascimento. Não era a dela." | `A new straw doll on the sacred tree with a small paper tag with different unreadable brush marks, grey morning light, + estilo` |
| H19_arvore_vazia_madrugada | "ninguém viu quem pregou" | `The sacred tree of the small shrine at 2 a.m., completely still, at the far edge three tiny candle flames just going out, nobody visible, + estilo` |

## O DOCUMENTÁRIO: os buracos

| Código | Fala | Prompt |
|---|---|---|
| N01_nurikabe_estrada | "O nurikabe é uma parede invisível…" | `A traveler with a paper lantern on a dark country road at night stopped by an invisible wall, the lantern light flattening against nothing, the traveler seen from behind, rice fields on the sides, + estilo` |
| N02_nurikabe_bastao | "A regra: pegue um pau e bata na parte de baixo." | `A traveler seen from behind sweeping a wooden walking stick low along the ground at the base of an invisible wall on a night road, dust flying, + estilo` |
| N03_jorogumo_cachoeira | "a jorōgumo… numa cachoeira de Izu…" | `A dark waterfall pool in a mountain forest, giant spider webs stretched between rocks and trees, a pale slender hand rising from the water holding out an old woodcutter's axe, a woodcutter seen from behind on the bank, + estilo` |
| N04_lenhador_teia_futon | "Dormiu… e não acordou mais." | `An old inn room at dawn, a sleeping figure under a futon completely covered by thin silk spider threads, sake cups knocked over beside it, face hidden under the cover, + estilo` |
| N05_oni_um_olho_campo | "um demônio de um olho só… come um homem que trabalhava no campo" | `A farmer seen from behind working a rice field at dusk, behind him a huge one-eyed oni with horns rising from the tall grass, + estilo` |
| N06_oni_chapeu_funeral | "no funeral de uma imperatriz, um oni de chapéu…" | `An ancient imperial funeral procession with banners winding through a misty valley, and on the ridge of a distant mountain a tall oni wearing a wide straw hat standing still and watching, + estilo` |
| N07_casa_canto_nordeste | "não põe porta, nem banheiro, nem cozinha no nordeste" | `The indented northeast corner of a traditional Japanese house, a patch of white gravel and a red-berried nandina bush planted exactly at the corner, + estilo` |
