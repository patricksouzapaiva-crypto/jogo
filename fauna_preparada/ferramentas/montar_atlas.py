"""Etapa 4: monta um atlas RGBA por especie + JSON com celula, pivot, ordem, tempos e alertas.
Tempos e velocidades sao SUGESTOES iniciais para teste (nao certificadas)."""
import json, os, sys, hashlib
from PIL import Image
PREP, OUT = sys.argv[1], sys.argv[2]
rel = json.load(open(os.path.join(PREP, "preparo.json")))
val = json.load(open(os.path.join(PREP, "validacao.json")))
os.makedirs(OUT, exist_ok=True)

ORDEM_WALK = ["down", "left", "right", "up"]
WALK_FPS = {"penala": 10, "pato": 9, "ovelha": 7, "gruntho": 8, "vaca": 6}
VEL_SUGERIDA = {"penala": 30, "pato": 22, "ovelha": 26, "gruntho": 32, "vaca": 20}
D_PADRAO = [0.12, 0.10, 0.16, 0.20, 0.14, 0.12]
DUR = {  # antecipacao curta, gesto principal mais longo, recuperacao
    "cabeca_baixa": [0.14, 0.12, 0.30, 0.40, 0.18, 0.14],
    "voz": [0.12, 0.10, 0.20, 0.28, 0.16, 0.12],
    "sacudir": [0.10, 0.07, 0.07, 0.07, 0.08, 0.14],
    "asas": [0.14, 0.14, 0.20, 0.36, 0.20, 0.14],
}
TIPO_ACAO = {"graze": "cabeca_baixa", "drink": "cabeca_baixa", "forage": "cabeca_baixa", "root": "cabeca_baixa",
             "peck": "cabeca_baixa", "scratch": None, "bleat": "voz", "moo": "voz", "cluck": "voz", "vocalize": "voz",
             "fleece_shake": "sacudir", "body_shake": "sacudir", "bristle_shake": "sacudir", "wing_stretch": "asas"}
LOOP_ACAO = {"ruminate": 3, "chew": 3, "tail_sway": 2}   # gestos que se repetem algumas vezes

# alertas confirmados na inspecao visual (alem das medidas automaticas)
ALERTAS_VISUAIS = {
    "vaca": {"walk_left": "Vista 3/4 e corpo curto; as acoes sao de perfil e compridas: a vaca muda de forma ao passar de andar para acao. Redesenhar a caminhada lateral de perfil (ou as acoes em 3/4).",
             "walk_right": "Mesmo problema da walk_left (3/4 x perfil). Quadro 0->1: topo sobe ~4 px.",
             "walk_up": "Quadro 1->2: cabeca e chifres crescem/sobem ~4 px (tamanho mudando entre quadros); manchas variam mais que nas outras direcoes."},
    "gruntho": {"walk_up": "Patas quase paradas (~5% de mudanca): so a traseira direita levanta (quadros 1,3,5,7); a esquerda quase nao. Vai parecer deslizar. Redesenhar com alternancia clara E/D.",
                "walk_down": "O passo aparece so nos quadros 1 e 4 (ritmo irregular)."},
    "penala": {"walk_down": "Quadros 7, 0 e 1 quase iguais (pes juntos): pausa perceptivel a cada ciclo.",
               "walk_up": "Pares 0-1 e 3-4 muito parecidos: pequenas pausas no ciclo."},
    "ovelha": {"walk_up": "Quadros 3~4 e 7~0 quase iguais: pequenas pausas no ciclo."},
}

manifest = {}
for esp, d in rel.items():
    W, H = d["canvas"]; px, py = d["pivot"]
    anims = []
    for dn in ORDEM_WALK: anims.append(("walk", dn))
    for q in d["quadros"]:
        if q["tipo"] == "actions" and ("actions", q["anim"]) not in anims: anims.append(("actions", q["anim"]))
    atlas = Image.new("RGBA", (W * 8, H * len(anims)), (0, 0, 0, 0))
    info = {}
    for li, (tipo, an) in enumerate(anims):
        qs = sorted([q for q in d["quadros"] if q["tipo"] == tipo and q["anim"] == an], key=lambda q: q["quadro"])
        for q in qs:
            atlas.alpha_composite(Image.open(os.path.join(PREP, esp, q["arquivo"])), (q["quadro"] * W, li * H))
        nome = f"walk_{an}" if tipo == "walk" else an
        v = val[esp][f"{tipo}:{an}"]
        alertas = list(v["alertas"])
        if nome in ALERTAS_VISUAIS.get(esp, {}): alertas.insert(0, "VISUAL: " + ALERTAS_VISUAIS[esp][nome])
        if tipo == "walk":
            fps = WALK_FPS[esp]
            info[nome] = dict(linha=li, quadros=len(qs), loop=True, duracoes=[round(1 / fps, 4)] * len(qs), fps=fps,
                              direcao=an, alertas=alertas)
        elif an == "idle_blink":
            info[nome] = dict(linha=li, quadros=len(qs), loop=True, duracoes=[0.12] * len(qs), direcao="right",
                              pausa_no_quadro_0=[1.5, 4.0], alertas=alertas,
                              obs="Fica no quadro 0 por um tempo aleatorio e entao toca o respirar/piscar.")
        else:
            dur = DUR.get(TIPO_ACAO.get(an) or "", D_PADRAO)
            info[nome] = dict(linha=li, quadros=len(qs), loop=False, duracoes=dur, direcao="right",
                              repeticoes=LOOP_ACAO.get(an, 1), volta_para="idle_blink",
                              intervalo_natural_s=[4, 12], alertas=alertas)
    pasta = os.path.join(OUT, esp); os.makedirs(pasta, exist_ok=True)
    fn_atlas = f"{esp}_atlas.png"; atlas.save(os.path.join(pasta, fn_atlas))
    meta = dict(especie=esp, atlas=fn_atlas, celula=[W, H], pivot=[px, py],
                pivot_obs="Ponto de contato com o chao dentro da celula. No Godot: centered=false e offset=-pivot.",
                altura_lado_px=d["altura_lado_px"], cores_na_paleta=d["cores"],
                fator_reducao=d["fator_reducao"], diferenca_escala_entre_folhas=d["diferenca_escala_entre_folhas"],
                velocidade_sugerida_px_s=VEL_SUGERIDA[esp],
                velocidade_obs="Estimativa inicial. Os ciclos nao tem um pe apoiado recuando de forma regular; ajustar a olho com o chao em movimento.",
                acoes_fornecidas_para="right",
                acoes_esquerda="PENDENTE: as acoes so existem viradas para a direita. Espelhar inverte a luz (cima-esquerda). Decidir: espelhar ou desenhar a esquerda.",
                animacoes=info,
                sha256_atlas=hashlib.sha256(open(os.path.join(pasta, fn_atlas), "rb").read()).hexdigest())
    json.dump(meta, open(os.path.join(pasta, f"{esp}.json"), "w"), indent=1, ensure_ascii=False)
    manifest[esp] = dict(json=f"{esp}/{esp}.json", atlas=f"{esp}/{fn_atlas}", celula=[W, H], pivot=[px, py])
    print(esp, atlas.size, len(anims), "animacoes")
json.dump(dict(pacote="FAUNA_PREPARADA_v1", origem="MOVIMENTACOES_DOS_ANIMAIS_v1", especies=manifest),
          open(os.path.join(OUT, "fauna_index.json"), "w"), indent=1, ensure_ascii=False)
