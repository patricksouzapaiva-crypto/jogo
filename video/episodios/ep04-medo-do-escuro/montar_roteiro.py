"""Monta roteiro.json do Ep. 04 "Não acenda a luz." a partir do ROTEIRO.md (cada fala "> ..." vira uma batida).
Regras da casa aplicadas (09/11):
- Vigia SÓ nas inserções (tema, Fyori, aparte, epílogo): "vigia_padrao": false + "com_vigia" nas cenas delas.
- Som sem sustos barulhentos: efeitos baixos, depois da palavra, no máximo ~1 a cada 30 s; trilha baixa e silêncio.
- Imagem nova a cada ~5–8 s na história, mais rápido no tema; vídeo real em ~1 a cada 4 cenas, nunca na revelação.
Uso: python3 montar_roteiro.py   (a narração precisa estar em audio/voz_completa.wav para renderizar)
"""
import json
import re
from pathlib import Path

AQUI = Path(__file__).parent

# ---------------------------------------------------------------- falas = linhas "> " do roteiro
md = (AQUI / "ROTEIRO.md").read_text(encoding="utf-8")
md = md[:md.index("## Fatos usados")]
falas = [re.sub(r"\*\(.*?\)\*", "", l[2:]).replace("**", "").strip() for l in md.splitlines() if l.startswith("> ")]
falas = [f for f in falas if f]
batidas = [{"fala": f} for f in falas]


def achar(t):
    for i, b in enumerate(batidas):
        if b["fala"].startswith(t) or t in b["fala"]:
            return i
    raise SystemExit("não achei: " + t)


# ---------------------------------------------------------------- tipos de cena
VIGIA = {"imagem": "../../painel/cenarios/abrigo_16x9.png", "vigia": True}


def vigia(z=(1.0, 1.04), foco=((0.55, 0.5), (0.57, 0.48))):
    return dict(VIGIA, zoom=list(z), foco=[list(foco[0]), list(foco[1])])


def img(nome, z=(1.0, 1.06), foco=None, **kw):
    pasta = "imagens" if nome.startswith("A") else "imagens_reais"
    ext = "png" if nome.startswith("A") else "jpg"
    c = {"imagem": f"{pasta}/{nome}.{ext}", "zoom": list(z), **kw}
    if foco:
        c["foco"] = [list(foco[0]), list(foco[1])]
    return c


def vid(nome, z=(1.0, 1.04), **kw):
    return {"video": f"videos/{nome}.mp4", "zoom": list(z), **kw}


def texto(t, vermelho=None, estilo="maquina", **kw):
    return {"tipo": "texto", "texto": t, "estilo": estilo, **({"vermelho": vermelho} if vermelho else {}), **kw}


def cartao(nome, legenda, giro=-1.5, video=False):
    c = vid(nome) if video else img(nome)
    c.update({"tipo": "cartao", "legenda_cartao": legenda, "giro": giro})
    return c


def C(trecho, *cenas, com_vigia=False):
    """Define as cenas da fala que começa com `trecho`. Cenas extras: (cena, "palavra onde entra")."""
    b = batidas[achar(trecho)]
    lista = []
    for x in cenas:
        c, em = (x if isinstance(x, tuple) else (x, None))
        c = dict(c)
        if em:
            c["em"] = em
        if com_vigia:
            c["com_vigia"] = True
        lista.append(c)
    b.pop("cena", None)
    if len(lista) == 1 and "em" not in lista[0]:
        b["cena"] = lista[0]
    else:
        b["cenas"] = lista


def T(trecho, entrada, dur=0.8):  # transição de entrada na 1ª cena da fala
    b = batidas[achar(trecho)]
    (b.get("cena") or b["cenas"][0]).update({"entrada": entrada, "duracao_entrada": dur})


def saida_lenta(trecho_seguinte, segurar, transicao="fundir", dur=1.6):
    """REGRA (usuário, 10/11): cena de tensão NÃO termina rápido nem com corte seco. A imagem tensa fica na tela
    `segurar` s em silêncio depois da última palavra e só então passa devagar (fundir/preto de `dur` s) para a
    próxima, terminando a transição quando a voz volta. Entrar na tensão pode ser corte seco; sair, nunca."""
    b = batidas[achar(trecho_seguinte)]
    b["pausa_antes_s"] = segurar + dur
    (b.get("cena") or b["cenas"][0]).update({"entrada": transicao, "duracao_entrada": dur, "antecipar": dur})


def pausa(trecho, s):
    batidas[achar(trecho)]["pausa_antes_s"] = s


def mus(trecho, som, db=-26, em=None):
    batidas[achar(trecho)]["musica"] = {"som": som, "volume_db": db, **({"em": em} if em else {})}


def fx(trecho, em, som, db, depois=True, atraso=0.0):
    batidas[achar(trecho)].setdefault("sons", []).append(
        {"em": em, "som": som, "volume_db": db, "depois": depois, "atraso": atraso})


def enf(trecho, em, pose, seg=1.8):
    batidas[achar(trecho)].setdefault("enfase", []).append({"em": em, "pose": pose, "segurar": seg})


# ================================================================ COLD OPEN (sem Vigia)
C("Ela ficou parada no escuro", img("A05_julia_cama", (1.0, 1.08), ((0.4, 0.5), (0.45, 0.48))))
C("Aos vinte, os olhos dela", img("A01_quarto_escuro", (1.0, 1.06)))
C("E foi aí que ela viu", img("A01_quarto_escuro", (1.12, 1.22), ((0.6, 0.45), (0.68, 0.42))))
C("que o canto do quarto", img("A01_quarto_escuro", (1.7, 1.8), ((0.71, 0.42), (0.71, 0.4))))   # corte seco no canto

# ================================================================ TEMA (Vigia apresenta; tipos de imagem alternando)
V = dict(com_vigia=True)
C("Toda criança já pediu", img("crianca_corredor_0", (1.0, 1.08), ((0.5, 0.5), (0.56, 0.48))), **V)
C("E quase todo adulto", vid("vela_apagando_1", (1.0, 1.03)), **V)
C("Por quê?", vigia((1.04, 1.08)))
C("Numa caverna da África do Sul", cartao("swartkrans_9", "Paranthropus robustus · Swartkrans, África do Sul"), **V)
C("Ele tem dois furos", cartao("swartkrans_10", "dois furos", giro=1.2), (vid("leopardo_v_1", (1.0, 1.05)), "leopardo"), **V)
C("Por milhões de anos", vid("leopardo_v_4", (1.0, 1.03)), **V)
C("Quem tinha medo do escuro", img("leopardo_3", (1.0, 1.08), ((0.5, 0.5), (0.45, 0.55))), (vigia((1.0, 1.04)), "Pra"), **V)
C("O corpo ainda lembra", texto("O corpo ainda lembra.\nNo escuro, o mesmo barulho assusta mais.", "lembra."))
C("Mas o escuro, em si", vigia((1.0, 1.05)))
C("O problema é o que a sua cabeça", img("canto_quarto_1", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45))), **V)
C("Lovecraft escreveu", cartao("lovecraft_4", "H. P. Lovecraft · 1934", giro=-1.2), **V)
C("E o escuro é o desconhecido", img("porta_apto_0", (1.0, 1.1), ((0.5, 0.5), (0.5, 0.45))), **V)
C("E tem um detalhe que quase", vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C("Quando a luz apaga, o seu olho", vid("pupila_2", (1.0, 1.04)), **V)
C("Até lá, você só vê uma parte", img("olho_escuro_2", (1.0, 1.1), ((0.6, 0.5), (0.68, 0.48))), **V)
C("Guarde esse número.", texto("20 MINUTOS", "20", "impacto", cps=10, tamanho=160))
C("Agora que você entende", vigia((1.06, 1.14), ((0.35, 0.45), (0.33, 0.42))))

# ================================================================ HISTÓRIA (o Vigia NÃO aparece daqui até a inserção)
C("A Júlia tinha vinte e nove anos", img("A12_julia_hospital", (1.0, 1.07), ((0.5, 0.5), (0.58, 0.5))))
T("A Júlia tinha vinte e nove anos", "preto", 1.2)
pausa("A Júlia tinha vinte e nove anos", 1.2)
fx("A Júlia tinha vinte e nove anos", "Júlia", "tecla", -18, depois=False, atraso=-1.0)   # clique do interruptor
C("Quando achou um apartamento", img("predio_antigo_4", (1.0, 1.06)), (img("predio_antigo_0", (1.0, 1.1), ((0.5, 0.6), (0.5, 0.4))), "pelo"))
C("Devia ter perguntado.", img("predio_antigo_0", (1.15, 1.22), ((0.5, 0.35), (0.5, 0.3))))
C("O prédio tinha um problema", vid("chuva_janela_v_0"), (vid("relampago_1"), "caía"))
C("Os vizinhos tinham lanterna", img("lampada_emergencia_1", (1.0, 1.08)))
C("Na primeira semana, ela foi trocar", img("quadro_luz_0", (1.0, 1.08)), (img("bilhete_1", (1.0, 1.08)), "papel"))
C('"Quando cair a energia, não acenda', texto("Quando cair a energia,\nnão acenda a luz. Nenhuma. Espere.", "luz."))
C("Ela riu.", img("quadro_luz_1", (1.0, 1.1)))

C("Duas semanas depois", vid("chuva_janela_v_2", (1.0, 1.04)))
C("A Júlia ia pegar o celular", img("A05_julia_cama", (1.0, 1.06)))
C("Sentou na cama e ficou olhando", img("A05_julia_cama", (1.12, 1.18), ((0.62, 0.45), (0.66, 0.42))))
C("Primeiro, preto total.", img("A01_quarto_escuro", (1.0, 1.05)))
T("Primeiro, preto total.", "preto", 2.5)   # o quarto "aparece" devagar, como o olho acostumando
C("Uns vinte minutos depois", img("A01_quarto_escuro", (1.05, 1.1), ((0.5, 0.5), (0.58, 0.47))))
C("E, no canto, entre o guarda-roupa", img("A01_quarto_escuro", (1.15, 1.35), ((0.6, 0.45), (0.7, 0.42))))
C("Alta. Fina demais. Parada.", img("A01_quarto_escuro", (1.75, 1.82), ((0.71, 0.42), (0.71, 0.4))))
C("Ela acendeu a lanterna.", img("A01_quarto_escuro", (1.75, 1.8), ((0.71, 0.42), (0.71, 0.4))), (img("A02_canto_lanterna", (1.0, 1.05)), "O"))
C("Só a parede.", img("A02_canto_lanterna", (1.1, 1.3), ((0.52, 0.6), (0.53, 0.68))))

# ---------------------------------------------------------------- inserção Fyori 1 (Vigia)
C("Em dois mil e dez", cartao("olho_escuro_0", "Giovanni Caputo · 2010 · a ilusão do rosto estranho"), **V)
C("Em menos de um minuto", vigia((1.0, 1.05)), (texto("um desconhecido.", "desconhecido.", "impacto", cps=12), "Outros"))
C("No escuro, o cérebro para", texto("No escuro, o cérebro para de esperar\ne começa a inventar.", "inventar."))
C("Foi exatamente isso", vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))

# ---------------------------------------------------------------- Ato 2 (sem Vigia)
C("Só que a forma não ficava", img("A03_janela", (1.0, 1.06)))
C("No apagão seguinte", img("A03_janela", (1.06, 1.1)), (img("A03b_janela", (1.1, 1.3), ((0.4, 0.4), (0.24, 0.38))), "Estava"))
C("No outro, ao lado da porta", img("A04_porta", (1.0, 1.06)))
C("E sempre do mesmo jeito", img("A04_porta", (1.06, 1.12), ((0.5, 0.5), (0.45, 0.48))), (img("A04_porta", (1.4, 1.5), ((0.74, 0.42), (0.74, 0.4))), "Mas"))

# ---------------------------------------------------------------- inserção Fyori 2 (Vigia)
C("Isso tem explicação.", img("estrelas_5", (1.0, 1.06)), **V)
C("Astrônomos aprendem cedo", vid("estrelas_v_5", (1.0, 1.05)), **V)
C("No escuro, o que está bem", texto("No escuro, o que está bem na sua frente\né o que você vê pior.", "pior."))

# ---------------------------------------------------------------- Ato 2 (sem Vigia)
C("A Júlia começou a anotar", img("caderno_1", (1.0, 1.08)))
C("Na quarta anotação", img("caderno_1", (1.15, 1.25), ((0.55, 0.5), (0.6, 0.45))))
C("A forma nunca aparecia longe", img("A03b_janela", (1.2, 1.4), ((0.3, 0.4), (0.22, 0.38))))
C("Numa tarde, mexendo na caixa", img("quadro_luz_1", (1.0, 1.1)), (img("caderno_3", (1.0, 1.06)), "caderno"))
C("Era do antigo morador.", img("caderno_3", (1.1, 1.2), ((0.4, 0.4), (0.38, 0.35))))
C("E dentro, o mesmo que ela", cartao("caderno_3", "caderno de Aurélio", giro=1.0))
C('"Quatro metros."', texto("4 metros.\n3 metros.\n2,5 metros.", "2,5 metros."))
C("As anotações iam por quase", img("caderno_3", (1.25, 1.4), ((0.55, 0.55), (0.6, 0.6))))
C('"Um metro."', texto("1 metro.\n70 centímetros.", "70 centímetros."))
C("A última linha estava escrita", img("caderno_3", (1.4, 1.55), ((0.6, 0.7), (0.62, 0.74))))
C('"Quarenta centímetros.', texto("40 centímetros.\nEla sorriu.", "sorriu.", "impacto", cps=12))
C("A página seguinte tinha", img("caderno_1", (1.0, 1.08)))
C('"Enquanto eu olho', texto("Enquanto eu olho, ela não anda.", "anda."))

C("A Júlia desceu e foi falar", img("corredor_predio_0", (1.0, 1.08), ((0.5, 0.6), (0.5, 0.5))))
C("Mostrou o caderno.", img("A06_dona_cida", (1.0, 1.04)))
C("A dona Cida ficou um tempo", img("A06_dona_cida", (1.05, 1.12), ((0.5, 0.5), (0.55, 0.45))))
C('"O seu Aurélio vivia de luz acesa', img("lampada_emergencia_1", (1.0, 1.08)), (img("A06_dona_cida", (1.15, 1.2), ((0.56, 0.42), (0.56, 0.4))), "Dizia"))
C('"Ela quem?"', img("A06_dona_cida", (1.2, 1.24), ((0.56, 0.42), (0.56, 0.4))))
C("A dona Cida não respondeu", vid("relampago_1", (1.0, 1.04)))
C("De manhã, o zelador achou", img("A01_quarto_escuro", (1.0, 1.08)), (texto("Vivo.", "Vivo.", "impacto", cps=10), "Vivo"))
C("Levaram ele pro hospital", img("hospital_quarto_6", (1.0, 1.08)))
C('"Pra qual hospital?"', img("A06_dona_cida", (1.0, 1.04)))
C("A dona Cida disse o nome", img("A06_dona_cida", (1.25, 1.32), ((0.56, 0.42), (0.56, 0.38))))
C("Era o hospital onde ela trabalhava", img("A12_julia_hospital", (1.1, 1.18), ((0.62, 0.5), (0.66, 0.48))))

# ---------------------------------------------------------------- aparte do Vigia (em destaque, trilha some)
C("Guarda essa frase do caderno", vigia((1.0, 1.05)))
C("Agora pensa no bilhete", texto("Não acenda a luz.", "luz."))
C("Porque a luz não faz ela ir embora", vigia((1.04, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C("E aí… ela anda.", texto("E aí… ela anda.", "anda.", "impacto", cps=12))
C("Não olha pro canto do seu quarto", vigia((1.1, 1.18), ((0.35, 0.42), (0.33, 0.4))))

# ---------------------------------------------------------------- Ato 3 — leito catorze (sem Vigia)
C("Na noite seguinte, no plantão", vid("monitor_v_5", (1.0, 1.03)))
C("Aurélio. Setenta e um anos", texto("AURÉLIO · 71 anos\nAla de longa permanência\nQuarto 4 · Leito 14", "14"))
C("Diagnóstico: estado catatônico", texto("Diagnóstico: estado catatônico.\nObs.: paciente não dorme!", "dorme!"))
C("As outras enfermeiras evitavam", img("hospital_quarto_2", (1.0, 1.08)))
C("Às duas da manhã, quando a ala", vid("luz_piscando_2", (1.0, 1.04)))
C("O quarto estava na penumbra", img("A07_aurelio", (1.0, 1.05)))
C("O seu Aurélio estava sentado", img("A07_aurelio", (1.1, 1.2), ((0.58, 0.48), (0.6, 0.45))), (img("A08_canto_hospital", (1.0, 1.06)), "Fixos"))
C("Ela chegou perto e sussurrou", img("A07b_aurelio_mao", (1.0, 1.08)))
C("Ele não se mexeu. Não piscou.", img("A07_aurelio", (1.3, 1.36), ((0.6, 0.45), (0.6, 0.43))))
C("Mas, depois de um tempo, a boca", img("A07_aurelio", (1.45, 1.52), ((0.6, 0.42), (0.6, 0.4))))
C('"Você apagou a luz."', texto("Você apagou a luz.", "luz."))
C("Não era uma pergunta.", img("A07b_aurelio_mao", (1.1, 1.18), ((0.62, 0.5), (0.65, 0.48))))
C('"Ela não mora no apartamento', img("A08_canto_hospital", (1.0, 1.12), ((0.5, 0.5), (0.6, 0.45))))
C("Os olhos dele não saíram", img("A07_aurelio", (1.2, 1.26), ((0.55, 0.45), (0.58, 0.44))))
C('"Faz oito meses que eu não durmo', img("A07b_aurelio_mao", (1.2, 1.3), ((0.66, 0.5), (0.68, 0.5))), (img("A08_canto_hospital", (1.2, 1.3), ((0.62, 0.45), (0.64, 0.44))), "ela"))
C("A Júlia olhou pro canto do quarto", img("A08_canto_hospital", (1.3, 1.5), ((0.62, 0.45), (0.64, 0.44))))
C('"E a minha?"', img("A07_aurelio", (1.5, 1.55), ((0.6, 0.42), (0.6, 0.4))))
C("Pela primeira vez, ele quase", img("A07_aurelio", (1.55, 1.6), ((0.6, 0.4), (0.6, 0.39))))
C('"A sua ficou em casa', img("A07_aurelio", (1.6, 1.62), ((0.6, 0.4), (0.6, 0.39))), (img("A01_quarto_escuro", (1.45, 1.75), ((0.66, 0.43), (0.71, 0.4))), "Esperando"))

# ---------------------------------------------------------------- inserção Fyori 3 (Vigia)
C("A gente pisca de quinze", vid("piscar_0", (1.0, 1.03)), **V)
C("Tente ficar sem piscar", vigia((1.0, 1.05)), (texto("dói.", "dói.", "impacto", cps=10), "dói"))
C("O corpo não foi feito", vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))

# ---------------------------------------------------------------- Ato 3 — a última noite (sem Vigia)
C("A Júlia não voltou pra casa", vid("luz_piscando_1", (1.0, 1.04)))
C("No terceiro dia, a dona Cida ligou", texto("CHAMADA RECEBIDA · 23:48\nDona Cida · 702", "702"))   # sem rosto: a dona Cida nunca aparece de frente
C('"Júlia, você tá em casa?"', img("corredor_predio_0", (1.1, 1.18), ((0.5, 0.55), (0.5, 0.45))))
C('"Não. Por quê?"', img("A12_julia_hospital", (1.2, 1.25), ((0.66, 0.5), (0.67, 0.48))))
C("Um silêncio comprido", img("corredor_predio_0", (1.25, 1.3), ((0.5, 0.42), (0.5, 0.4))))
C('"Porque toda noite eu escuto', img("A04_porta", (1.0, 1.15), ((0.5, 0.5), (0.57, 0.45))))
C("Mas ela tinha que voltar", img("predio_antigo_4", (1.0, 1.06)))
C("Voltou numa sexta à noite", vid("chuva_janela_v_0", (1.0, 1.04)))
C("Às onze e vinte, a luz caiu", vid("relampago_1", (1.0, 1.04)), (texto("No bairro inteiro.", "inteiro."), "No"))
C("Dessa vez, ela não acendeu nada", img("A05_julia_cama", (1.0, 1.06)))
C("Contou os minutos.", img("A05_julia_cama", (1.15, 1.2), ((0.4, 0.45), (0.42, 0.43))))
C("Aos vinte, ela viu.", img("A01_quarto_escuro", (1.0, 1.04)))
C("Não estava no canto.", img("A01_quarto_escuro", (1.04, 1.06)), (img("A10_dois_passos", (1.0, 1.05)), "Estava"))
C("Alta. Fina demais. O rosto", img("A10_dois_passos", (1.1, 1.3), ((0.5, 0.45), (0.48, 0.3))))
C("A Júlia não piscou.", img("A10_dois_passos", (1.0, 1.02)))
C("Ficaram assim.", img("A10_dois_passos", (1.02, 1.04)))
C("Os olhos dela ardiam", img("A10_dois_passos", (1.04, 1.12), ((0.48, 0.45), (0.48, 0.4))))   # fica NA criatura (sem cortar pro olho)
C("Ela piscou uma vez", texto(" ", estilo="maquina"), (img("A10_dois_passos", (1.35, 1.4), ((0.48, 0.38), (0.48, 0.36))), "Quando"))
C("Ela mordeu a boca", img("A10_dois_passos", (1.4, 1.48), ((0.48, 0.36), (0.48, 0.34))))
C("Às quatro e pouco da manhã", img("A05_julia_cama", (1.2, 1.25), ((0.4, 0.45), (0.42, 0.43))))
C("Os olhos fecharam sozinhos", texto("Um segundo.\nTalvez dois.", "dois."))
C("E, no escuro atrás das pálpebras", texto(" ", estilo="maquina"))
C("Ela abriu os olhos.", texto(" ", estilo="maquina"))
C("Dessa vez, não precisou esperar", img("A10_dois_passos", (2.1, 2.2), ((0.48, 0.3), (0.48, 0.29))))   # o rosto, perto demais

# ================================================================ EPÍLOGO (Vigia volta: é o respiro)
C("Na segunda-feira, a ala", vigia((1.0, 1.04)))
C("Vinte e nove anos. Enfermeira", img("A11_leitos", (1.0, 1.06)))
C("Puseram ela no quarto quatro", img("A11_leitos", (1.1, 1.2), ((0.55, 0.5), (0.6, 0.48))))
C("As enfermeiras do turno da noite", img("A11_leitos", (1.2, 1.28), ((0.5, 0.5), (0.52, 0.5))))
C("Cada um olhando pra um canto", img("A11_leitos", (1.35, 1.4), ((0.52, 0.5), (0.52, 0.5))))
C("E o apartamento do sétimo andar", vigia((1.0, 1.05)))
C("Dizem que a dona Cida colou", img("quadro_luz_0", (1.0, 1.1)), **V)
C('"Quando cair a energia, não acenda a luz. Espere. E nunca', texto("Quando cair a energia, não acenda a luz.\nEspere. E nunca feche os olhos.", "olhos."))
C("Hoje, quando você apagar a luz", vigia((1.05, 1.1), ((0.4, 0.45), (0.38, 0.42))))
C("E se antes dos vinte minutos", img("A01_quarto_escuro", (1.0, 1.06)), (vigia((1.15, 1.2), ((0.35, 0.42), (0.34, 0.4))), "não"))
C("Você piscou agora", vigia((1.2, 1.24), ((0.34, 0.42), (0.34, 0.4))))
C("Me conta nos comentários", vigia((1.0, 1.04)))

# ================================================================ SAÍDAS LENTAS das cenas de tensão
pausa("Ela acendeu a lanterna.", 1.2)                       # segura o quarto escuro antes da lanterna
saida_lenta("Em dois mil e dez", 1.2, "fundir", 1.4)       # marca no rodapé -> inserção 1
saida_lenta("Isso tem explicação.", 1.2, "fundir", 1.4)    # forma ao lado da porta -> inserção 2
saida_lenta("Numa tarde, mexendo na caixa", 1.0, "fundir", 1.2)   # "cada vez mais perto"
saida_lenta("A página seguinte tinha", 1.8, "fundir", 1.4)        # "Ela sorriu."
saida_lenta("A Júlia desceu e foi falar", 1.2, "fundir", 1.4)     # "enquanto eu olho, ela não anda"
saida_lenta("Levaram ele pro hospital", 0.8, "fundir", 1.2)       # "Vivo."
saida_lenta("Guarda essa frase do caderno", 1.5, "preto", 1.6)    # "era o hospital onde ela trabalhava"
saida_lenta("Na noite seguinte, no plantão", 1.5, "preto", 1.6)   # fim do aparte
saida_lenta("A gente pisca de quinze", 3.2, "fundir", 2.2)        # "A sua ficou em casa. Esperando você." (pedido do usuário)
saida_lenta("Dessa vez, ela não acendeu nada", 1.0, "fundir", 1.4)  # "No bairro inteiro."
saida_lenta("Às quatro e pouco da manhã", 0.8, "fundir", 1.6)    # sai da criatura devagar
saida_lenta("Os olhos fecharam sozinhos", 0.3, "fundir", 1.8)    # os olhos fechando = a tela escurece devagar
saida_lenta("Na segunda-feira, a ala", 3.0, "preto", 2.0)        # o rosto da forma fica; depois, o respiro
saida_lenta("E o apartamento do sétimo andar", 1.8, "fundir", 1.6)  # "cada um olhando pra um canto"

# ================================================================ trilha (baixa; silêncio nos momentos-chave)
mus("Ela ficou parada no escuro", "drone_terror", -30)
mus("Toda criança já pediu", "trilha_tensa_1", -28)
mus("A Júlia tinha vinte e nove anos", "drone_tensao", -28)
mus("Duas semanas depois", "silencio")
mus("Primeiro, preto total.", "drone_terror", -28)
mus("Ela acendeu a lanterna.", "silencio")
mus("Em dois mil e dez", "trilha_tensa_1", -30)
mus("Só que a forma não ficava", "trilha_tensa_2", -28)
mus("Isso tem explicação.", "trilha_tensa_1", -30)
mus("A Júlia começou a anotar", "drone_tensao", -28)
mus('"Quatro metros."', "drone_terror", -28)
mus('"Quarenta centímetros.', "silencio")
mus("A Júlia desceu e foi falar", "trilha_tensa_1", -28)
mus("Guarda essa frase do caderno", "silencio")
mus("Na noite seguinte, no plantão", "drone_tensao", -28)
mus("O quarto estava na penumbra", "drone_terror", -28)
mus('"A sua ficou em casa', "silencio", em="Esperando")
mus("A gente pisca de quinze", "trilha_tensa_1", -30)
mus("A Júlia não voltou pra casa", "trilha_tensa_2", -28)
mus("Às onze e vinte, a luz caiu", "silencio", em="No")
mus("Aos vinte, ela viu.", "drone_terror", -26)
mus("Os olhos fecharam sozinhos", "silencio")
mus("Na segunda-feira, a ala", "trilha_tensa_1", -28)
mus('"Quando cair a energia, não acenda a luz. Espere. E nunca', "silencio")
mus("Hoje, quando você apagar a luz", "trilha_tensa_1", -30)

# ================================================================ efeitos (baixos, depois da palavra, ~1 a cada 30 s)
fx("que o canto do quarto", "esteve", "sub_drop", -12)
fx("Alta. Fina demais. Parada.", "Parada", "riser_tensao", -14)
fx("Ela acendeu a lanterna.", "lanterna", "tecla", -18, depois=False)
fx("No outro, ao lado da porta", "quarto", "sub_drop", -14)
fx('"Quarenta centímetros.', "sorriu", "sub_drop", -12)
fx("De manhã, o zelador achou", "Vivo", "sub_drop", -16)
fx("Era o hospital onde ela trabalhava", "trabalhava", "riser_tensao", -14)
fx('"Você apagou a luz."', "luz", "sub_drop", -14)
fx('"A sua ficou em casa', "você", "sub_drop", -12)
fx('"Porque toda noite eu escuto', "porta", "passos_atrasados", -10)
fx("Não estava no canto.", "cama", "sub_drop", -10)
fx("Ela piscou uma vez", "passo", "stinger_cordas", -14)
fx("E, no escuro atrás das pálpebras", "perto", "respiracao_nuca", -8)
fx("Dessa vez, não precisou esperar", "minutos", "sub_drop", -12)

# ================================================================ ênfases do Vigia (só onde ele aparece)
enf("Por quê?", "Por", "c_pensativo_queixo", 2.0)
enf("Mas o escuro, em si", "Mas", "c_dedo_explicando", 1.8)
enf("E tem um detalhe que quase", "detalhe", "c_sussurrando", 2.0)
enf("Agora que você entende", "Agora", "s_sorriso_sombrio", 2.2)
enf("Foi exatamente isso", "exatamente", "c_desconfiado_lado", 1.8)
enf("Guarda essa frase do caderno", "Guarda", "c_dedo_explicando", 1.8)
enf("Porque a luz não faz ela ir embora", "parar", "s_encarando", 2.0)
enf("Não olha pro canto do seu quarto", "Não", "s_silencio", 2.2)
enf("Não olha pro canto do seu quarto", "olha.", "s_encarando", 2.4)
enf("O corpo não foi feito", "corpo", "c_serio_frontal", 1.8)
enf("Na segunda-feira, a ala", "segunda-feira", "c_cafe_explica", 2.0)
enf("E o apartamento do sétimo andar", "baratinho", "s_sorriso_sombrio", 2.0)
enf("Hoje, quando você apagar a luz", "conta", "c_cafe_indicador", 1.8)
enf("Você piscou agora", "piscou", "s_sorriso_sombrio", 2.4)
enf("Me conta nos comentários", "Me", "c_cafe_convite", 2.2)

roteiro = {
    "modo": "cenas", "formato": "16:9", "tema": "vigia", "avatar": "vigia_hd",
    "voz_arquivo": "audio/voz_completa.wav", "apertar_pausas": False,
    "vigia_padrao": False,
    "preencher_pausas": {"min": 1.3},
    "cauda": 1.6, "chuva": 0, "grao": 0.14,
    "mix": {"musica_ganho_db": 12, "fundo_sob_voz": -9, "efeitos_sob_voz": -4},
    "legendas": {"destaques": ["luz", "canto", "perto", "vinte", "olhos", "escuro"]},
    "ambiente_inicial": [], "musica": {"som": "silencio", "volume_db": -40},
    "abertura": {"texto": "O VIGIA\nEP. 04 · NÃO ACENDA A LUZ.", "vermelho": "LUZ.", "duracao": 3.2,
                 "segurar": 1.8,   # o canto do quarto fica na tela em silêncio antes do cartão
                 "antes_da_batida": achar("Toda criança já pediu"),
                 "sons": [{"som": "sub_drop", "t": 0.2, "volume_db": -12}]},
    "cta": {"titulo": "Você dorme de luz acesa?", "canal": "Último Abrigo",
            "subtitulo": "Inscreva-se para mais casos do Vigia",
            "fundo": "../../painel/cenarios/abrigo_16x9.png", "pose": "c_cafe_convite", "duracao": 3.8},
    "batidas": batidas,
}
for b in batidas:  # tela de texto não leva legenda (o texto já está na tela)
    for c in ([b["cena"]] if b.get("cena") else []) + b.get("cenas", []):
        if c.get("tipo") == "texto" and "em" not in c:
            b["sem_legenda"] = True

# conferências: arquivos existem e toda fala da história tem cena em algum momento
faltando = []
for b in batidas:
    for c in ([b["cena"]] if b.get("cena") else []) + b.get("cenas", []):
        for k in ("imagem", "video"):
            if c.get(k) and not (AQUI / c[k]).exists():
                faltando.append(c[k])
if faltando:
    raise SystemExit("arquivos faltando: " + ", ".join(sorted(set(faltando))))
sem = [i for i, b in enumerate(batidas) if not (b.get("cena") or b.get("cenas"))]
(AQUI / "roteiro.json").write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
n_cenas = sum(1 + len(b.get("cenas", [])) - (1 if b.get("cenas") else 0) for b in batidas if b.get("cena") or b.get("cenas"))
print(f"{len(batidas)} falas, {n_cenas} cenas, falas que continuam a cena anterior: {len(sem)}")
