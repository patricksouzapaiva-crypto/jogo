## Verificacao automatica (rodar sem abrir o editor):
##   godot --headless --path <pasta do projeto> --script res://testes/heroi/verificar_heroi.gd
## Confere atlas/JSON e simula as transicoes da cena de teste. Nao altera nada.
extends SceneTree

var falhas := 0


func _ok(cond: bool, msg: String) -> void:
	if cond:
		print("  OK    ", msg)
	else:
		falhas += 1
		print("  FALHA ", msg)


func _initialize() -> void:
	print("== Dados")
	var d := CarregadorHeroi.carregar()
	_ok(not d.is_empty(), "heroi.json carregado")
	if d.is_empty():
		quit(1)
		return
	_ok(int(d["celula"][0]) == 48 and int(d["celula"][1]) == 72, "celula 48x72 (mesmo tamanho do personagem atual)")
	var sf := CarregadorHeroi.montar_sprite_frames(d)
	for dir in ["down", "left", "right", "up"]:
		for tipo in ["walk", "idle"]:
			var nome: String = tipo + "_" + dir
			var esperado := 8 if tipo == "walk" else 2
			_ok(sf.has_animation(nome) and sf.get_frame_count(nome) == esperado, "%s: %d quadros" % [nome, esperado])
			if not sf.has_animation(nome):
				continue
			var vazio := 0
			var fora := 0
			for i in sf.get_frame_count(nome):
				var t: AtlasTexture = sf.get_frame_texture(nome, i)
				var img := t.atlas.get_image().get_region(Rect2i(t.region))
				if img.is_invisible():
					vazio += 1
				# os pes encostam na linha do pivo: a linha logo acima do pivo tem pixel
				var py: int = d["pivot"][1]
				var tem := false
				for x in img.get_width():
					if img.get_pixel(x, py - 1).a > 0.5:
						tem = true
						break
				if not tem and tipo == "idle":
					fora += 1
			_ok(vazio == 0, "%s: nenhum quadro vazio" % nome)
			if tipo == "idle":
				_ok(fora == 0, "%s: pes no chao (linha do pivo)" % nome)
		var dur: Array = d["animacoes"]["walk_" + dir]["duracoes"]
		_ok(absf(float(dur[0]) - 0.075) < 0.0001, "walk_%s: 75 ms por quadro" % dir)
	var img_atlas: Image = sf.get_frame_texture("walk_down", 0).atlas.get_image()
	var semi := 0
	for y in img_atlas.get_height():
		for x in img_atlas.get_width():
			var al := img_atlas.get_pixel(x, y).a
			if al > 0.01 and al < 0.99:
				semi += 1
	_ok(semi == 0, "alpha sem semi-transparencia (pixel nitido)")
	await process_frame

	print("== Transicoes na cena de teste")
	var cena: Node2D = load("res://testes/heroi/teste_heroi.tscn").instantiate()
	cena.demonstracao = false
	root.add_child(cena)
	await process_frame
	var s: AnimatedSprite2D = cena.heroi
	_ok(s.animation == &"idle_down" and s.is_playing(), "comeca parado olhando para baixo (respirando)")
	var inicio := CarregadorHeroi.quadro_inicio(d, "right")
	Input.action_press("ui_right")
	await process_frame
	_ok(s.animation == &"walk_right" and (s.frame == inicio or s.frame == (inicio + 1) % 8),
		"parado -> andar para a direita comeca no quadro %d (visto %d)" % [inicio, s.frame])
	var x0: float = cena.posicao.x
	var t0 := Time.get_ticks_msec()
	for i in 30: await process_frame
	var dt := (Time.get_ticks_msec() - t0) / 1000.0
	_ok(cena.posicao.x > x0, "anda para a direita (andou %.1f px em %.2f s)" % [cena.posicao.x - x0, dt])
	var q := s.frame
	Input.action_press("ui_up")
	Input.action_release("ui_right")
	await process_frame
	_ok(s.animation == &"walk_up", "troca de direcao andando: direita -> cima")
	_ok(absi(s.frame - q) <= 1 or absi(s.frame - q) == 7, "na troca continua no mesmo ponto do passo (%d -> %d)" % [q, s.frame])
	Input.action_release("ui_up")
	await process_frame
	_ok(s.animation == &"idle_up" and s.frame <= 1, "solta a tecla: para e respira olhando para cima")
	Input.action_press("ui_left")
	await process_frame
	Input.action_release("ui_left")
	await process_frame
	_ok(s.animation == &"idle_left", "toque rapido para a esquerda: vira e fica parado olhando para a esquerda")
	cena.demonstracao = true
	var vistas := {}
	var t_ini := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t_ini < 14000:      # o roteiro completo leva ~13 s
		await process_frame
		vistas[String(s.animation)] = true
	_ok(vistas.size() == 8, "modo demonstracao passa por andar e parado nas direcoes (%s)" % ", ".join(vistas.keys()))
	print("== Resultado: %s" % ("TUDO OK" if falhas == 0 else "%d FALHA(S)" % falhas))
	quit(falhas)
