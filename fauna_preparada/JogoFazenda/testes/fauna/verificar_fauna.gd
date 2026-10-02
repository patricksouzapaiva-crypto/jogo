## Verificacao automatica (rodar sem abrir o editor):
##   godot --headless --path <pasta do projeto> --script res://testes/fauna/verificar_fauna.gd
## Confere atlas/JSON e simula as transicoes da cena de teste. Nao altera nada.
extends SceneTree

var falhas := 0


func _ok(cond: bool, msg: String) -> void:
	if cond:
		print("  OK   ", msg)
	else:
		falhas += 1
		print("  FALHA ", msg)


func _initialize() -> void:
	print("== Dados")
	var dados := CarregadorFauna.carregar_tudo()
	_ok(dados.size() == 5, "5 especies carregadas (%d)" % dados.size())
	for e in dados:
		var sf := CarregadorFauna.montar_sprite_frames(dados[e])
		var d: Dictionary = dados[e]
		for nome in d["animacoes"]:
			var a: Dictionary = d["animacoes"][nome]
			_ok(sf.has_animation(nome) and sf.get_frame_count(nome) == int(a["quadros"]),
				"%s/%s: %d quadros" % [e, nome, int(a["quadros"])])
			var vazio := 0
			for i in sf.get_frame_count(nome):
				var t: AtlasTexture = sf.get_frame_texture(nome, i)
				var img := t.atlas.get_image().get_region(Rect2i(t.region))
				if img.is_invisible():
					vazio += 1
			_ok(vazio == 0, "%s/%s: nenhum quadro vazio" % [e, nome])
		var img_atlas: Image = sf.get_frame_texture(d["animacoes"].keys()[0], 0).atlas.get_image()
		var semi := 0
		for y in range(0, img_atlas.get_height(), 3):
			for x in range(0, img_atlas.get_width(), 3):
				var al := img_atlas.get_pixel(x, y).a
				if al > 0.01 and al < 0.99:
					semi += 1
		_ok(semi == 0, "%s: alpha sem semi-transparencia" % e)
	await process_frame
	print("== Transicoes na cena de teste")
	var cena: Node2D = load("res://testes/fauna/teste_fauna.tscn").instantiate()
	root.add_child(cena)
	await process_frame
	var s: AnimatedSprite2D = cena.animais[0]
	_ok(s.is_playing(), "cena abriu e a animacao esta tocando (%s)" % s.animation)
	Input.action_press("ui_right")
	await process_frame
	var par_dir: int = int(cena.dados["penala"]["animacoes"]["walk_right"].get("parado", 0))
	# tolera 1 passo: no primeiro quadro do motor a animacao pode ja ter avancado
	var esperado := (par_dir + 1) % 8
	_ok(s.animation == &"walk_right" and (s.frame == esperado or s.frame == (esperado + 1) % 8),
		"parado -> andar comeca logo depois da pose de parado (quadro %d, visto %d)" % [esperado, s.frame])
	for i in 10: await process_frame
	_ok(s.animation == &"walk_right" and s.is_playing(), "parado -> andar para a direita")
	var q0 := s.frame
	for i in 30: await process_frame
	_ok(s.animation == &"walk_right", "caminhada nao reinicia a cada quadro (quadro %d -> %d)" % [q0, s.frame])
	Input.action_release("ui_right")
	Input.action_press("ui_up")
	for i in 5: await process_frame
	_ok(s.animation == &"walk_up", "troca de direcao: direita -> cima")
	Input.action_release("ui_up")
	for i in 5: await process_frame
	var par_cima: int = int(cena.dados["penala"]["animacoes"]["walk_up"].get("parado", 0))
	_ok(s.animation == &"walk_up" and not s.is_playing() and s.frame == par_cima, "andar -> parado (cima segura a pose de parado, quadro %d)" % par_cima)
	Input.action_press("ui_right")
	for i in 3: await process_frame
	Input.action_release("ui_right")
	for i in 5: await process_frame
	_ok(s.animation == &"idle_blink", "andar -> parado (direita usa respirar/piscar)")
	cena.acao_escolhida = cena._lista_acoes("penala")[0]
	cena._tocar_acao()
	await process_frame
	_ok(String(s.animation) == cena.acao_escolhida, "parado -> acao (%s)" % cena.acao_escolhida)
	var t0 := Time.get_ticks_msec()
	while String(s.animation) == cena.acao_escolhida and Time.get_ticks_msec() - t0 < 5000:
		await process_frame
	_ok(s.animation == &"idle_blink", "acao -> volta para respirar/piscar")
	cena._tocar_acao()
	for i in 3: await process_frame
	Input.action_press("ui_left")
	for i in 5: await process_frame
	_ok(s.animation == &"walk_left", "acao interrompida por deslocamento")
	Input.action_release("ui_left")
	cena.ui_especie.select(cena.ui_especie.item_count - 1)
	cena.ui_especie.item_selected.emit(cena.ui_especie.item_count - 1)
	for i in 3: await process_frame
	_ok(cena.animais.size() == 5, "modo comparar mostra os 5 animais")
	print("== Resultado: %s (%d falhas)" % ["PASSOU" if falhas == 0 else "FALHOU", falhas])
	quit(1 if falhas else 0)
