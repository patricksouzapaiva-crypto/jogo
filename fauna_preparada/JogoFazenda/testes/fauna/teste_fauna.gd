## Cena de TESTE das animacoes da fauna (isolada e reversivel: apague a pasta
## res://testes/fauna para remover). Nao altera nenhuma regra do jogo.
##
## Teclado: setas/WASD = andar (testa parado -> andar -> parado e troca de direcao)
##          E = tocar a acao escolhida (andar durante a acao interrompe a acao)
##          Espaco = tocar/pausar   , e . = quadro anterior/proximo
extends Node2D

@export var pasta_fauna := "res://arte/preparado/fauna"
## Coloque aqui a textura do chao do jogo para testar sobre o terreno real.
@export var textura_terreno: Texture2D

const ESPECIES := ["penala", "pato", "ovelha", "gruntho", "vaca"]
const DIRECOES := {"down": Vector2.DOWN, "left": Vector2.LEFT, "right": Vector2.RIGHT, "up": Vector2.UP}

var dados := {}
var frames := {}
var especie := "penala"
var comparar := false
var animais: Array[AnimatedSprite2D] = []
var anim_escolhida := "walk_right"
var acao_escolhida := ""
var repeticoes_restantes := 0
var andando := false
var direcao := "right"
var modo_natural := false
var espelhar_acoes := false
var mostrar_pivot := true
var chao_px_s := 0.0
var fundo := "terreno"
var zoom := 4.0
var zoom_efetivo := 4.0
var tempo_ate_acao := 6.0

var mundo: Node2D
var marcas: Node2D
var chao: Sprite2D
var painel: PanelContainer
var ui_especie: OptionButton
var ui_anim: OptionButton
var ui_acao: OptionButton
var ui_info: Label
var ui_vel: HSlider
var ui_chao: HSlider
var ui_chao_txt: Label
var _scroll := Vector2.ZERO
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.randomize()
	dados = CarregadorFauna.carregar_tudo(pasta_fauna)
	for e in dados:
		frames[e] = CarregadorFauna.montar_sprite_frames(dados[e])
	mundo = Node2D.new()
	add_child(mundo)
	chao = Sprite2D.new()
	chao.centered = true
	chao.region_enabled = true
	chao.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	chao.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	mundo.add_child(chao)
	marcas = Node2D.new()          # pivot e caixa, desenhados por cima dos animais
	marcas.z_index = 100
	add_child(marcas)
	marcas.draw.connect(_desenhar_marcas)
	_montar_ui()
	_aplicar_fundo()
	_recriar_animais()
	get_viewport().size_changed.connect(_reposicionar)
	_reposicionar()


# ------------------------------------------------------------------ animais
func _recriar_animais() -> void:
	for a in animais:
		a.queue_free()
	animais.clear()
	var lista := ESPECIES.filter(func(e): return dados.has(e)) if comparar else [especie]
	var x := 0.0
	var larguras := []
	for e in lista:
		larguras.append(float(dados[e]["celula"][0]))
	var total := 0.0
	for l in larguras:
		total += l
	x = -total / 2.0
	for i in lista.size():
		var e: String = lista[i]
		var s := AnimatedSprite2D.new()
		s.sprite_frames = frames[e]
		s.centered = false
		s.offset = CarregadorFauna.offset_do_pivot(dados[e])
		s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		s.set_meta("especie", e)
		s.position = Vector2(x + float(dados[e]["pivot"][0]), 0) if comparar else Vector2.ZERO
		x += larguras[i]
		s.animation_finished.connect(_ao_terminar.bind(s))
		s.animation_looped.connect(_ao_repetir.bind(s))
		s.frame_changed.connect(marcas.queue_redraw)
		mundo.add_child(s)
		animais.append(s)
	_preencher_listas()
	_reposicionar()
	_tocar(anim_escolhida, true)


func _tocar(nome: String, forcar := false) -> void:
	for s in animais:
		var e: String = s.get_meta("especie")
		var flip := false
		var real := nome
		if not s.sprite_frames.has_animation(real):
			continue
		if not real.begins_with("walk_") and direcao == "left":
			flip = espelhar_acoes
		s.flip_h = flip
		# nao reinicia a animacao a cada atualizacao: so troca quando muda
		if forcar or s.animation != StringName(real) or not s.is_playing():
			s.play(real)
	anim_escolhida = nome
	if ui_anim:
		for i in ui_anim.item_count:
			if ui_anim.get_item_text(i) == nome and ui_anim.selected != i:
				ui_anim.select(i)
	_atualizar_info()


func _parado_na_direcao() -> void:
	# Pacote atual: respirar/piscar so existe virado para a direita.
	# Para baixo/cima/esquerda (sem espelhar) segura o 1o quadro da caminhada.
	if direcao == "right" or (direcao == "left" and espelhar_acoes):
		_tocar("idle_blink")
	else:
		# segura a pose de parado da direcao (patas juntas, dois pes no chao)
		_tocar("walk_" + direcao, true)
		for s in animais:
			s.pause()
			s.frame = _quadro_parado(s, direcao)


func _quadro_parado(s: AnimatedSprite2D, dir: String) -> int:
	var e: String = s.get_meta("especie")
	return int(dados[e]["animacoes"]["walk_" + dir].get("parado", 0))


func _ao_repetir(s: AnimatedSprite2D) -> void:
	# pausa natural no quadro 0 do respirar/piscar (tempo aleatorio a cada volta)
	if s.animation == &"idle_blink":
		var e: String = s.get_meta("especie")
		var p: Array = dados[e]["animacoes"]["idle_blink"].get("pausa_no_quadro_0", [0.12, 0.12])
		var t: Texture2D = s.sprite_frames.get_frame_texture(&"idle_blink", 0)
		var dur := _rng.randf_range(p[0], p[1]) if modo_natural else 0.12
		s.sprite_frames.set_frame(&"idle_blink", 0, t, dur)


func _ao_terminar(s: AnimatedSprite2D) -> void:
	if s != animais[0]:
		return
	if repeticoes_restantes > 1:
		repeticoes_restantes -= 1
		_tocar(anim_escolhida, true)
	elif not andando and not anim_escolhida.begins_with("walk_"):
		_parado_na_direcao()


func _tocar_acao() -> void:
	if acao_escolhida == "" or andando:
		return
	var e: String = animais[0].get_meta("especie")
	repeticoes_restantes = int(dados[e]["animacoes"][acao_escolhida].get("repeticoes", 1))
	_tocar(acao_escolhida, true)


# ------------------------------------------------------------------ loop
func _process(delta: float) -> void:
	var v := Vector2.ZERO
	if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_A): v.x -= 1
	if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D): v.x += 1
	if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_W): v.y -= 1
	if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S): v.y += 1
	if v != Vector2.ZERO:
		var nova := "right" if v.x > 0 else "left" if v.x < 0 else ("down" if v.y > 0 else "up")
		var mudou := (not andando) or nova != direcao
		andando = true
		direcao = nova
		repeticoes_restantes = 0
		if mudou:
			_tocar("walk_" + direcao, true)
			# comeca a andar do quadro seguinte a pose de parado (sem "pulo" no 1o passo)
			for s in animais:
				var n := s.sprite_frames.get_frame_count(s.animation)
				s.frame = (_quadro_parado(s, direcao) + 1) % n
		# o mundo anda sob o animal (a camera acompanha o animal)
		var e: String = animais[0].get_meta("especie")
		var vel: float = float(dados[e]["velocidade_sugerida_px_s"]) * ui_vel.value
		_scroll += DIRECOES[direcao] * vel * delta
	elif andando:
		andando = false
		_parado_na_direcao()
	elif chao_px_s > 0.0 and anim_escolhida.begins_with("walk_"):
		# teste de escorregar: chao andando sob a caminhada parada no lugar
		_scroll += DIRECOES[anim_escolhida.trim_prefix("walk_")] * chao_px_s * delta
	if modo_natural and not andando and not comparar:
		tempo_ate_acao -= delta
		if tempo_ate_acao <= 0.0 and animais[0].animation == &"idle_blink":
			var acoes := _lista_acoes(animais[0].get_meta("especie"))
			if acoes.size() > 0:
				acao_escolhida = acoes[_rng.randi() % acoes.size()]
				_tocar_acao()
			var e2: String = animais[0].get_meta("especie")
			var faixa: Array = [4, 12]
			if dados[e2]["animacoes"].has(acao_escolhida):
				faixa = dados[e2]["animacoes"][acao_escolhida].get("intervalo_natural_s", [4, 12])
			tempo_ate_acao = _rng.randf_range(faixa[0], faixa[1])
	chao.region_rect = Rect2(_scroll, chao.region_rect.size)
	marcas.queue_redraw()


func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		match ev.keycode:
			KEY_E: _tocar_acao()
			KEY_SPACE: _alternar_pausa()
			KEY_COMMA: _passo(-1)
			KEY_PERIOD: _passo(1)


func _alternar_pausa() -> void:
	for s in animais:
		if s.is_playing(): s.pause()
		else: s.play()
	_atualizar_info()


func _passo(d: int) -> void:
	for s in animais:
		s.pause()
		var n := s.sprite_frames.get_frame_count(s.animation)
		s.frame = posmod(s.frame + d, n)
	_atualizar_info()


# ------------------------------------------------------------------ desenho (pivot e caixa)
func _desenhar_marcas() -> void:
	if not mostrar_pivot:
		return
	for s in animais:
		var e: String = s.get_meta("especie")
		var p := s.global_position
		var w := float(dados[e]["celula"][0]) * zoom_efetivo
		var h := float(dados[e]["celula"][1]) * zoom_efetivo
		var o := s.offset * zoom_efetivo
		var x0 := p.x + (o.x if not s.flip_h else -(o.x + w))
		marcas.draw_rect(Rect2(x0, p.y + o.y, w, h), Color(1, 1, 1, 0.35), false, 1.0)
		marcas.draw_line(p + Vector2(-6, 0), p + Vector2(6, 0), Color.RED, 2.0)
		marcas.draw_line(p + Vector2(0, -6), p + Vector2(0, 6), Color.RED, 2.0)


# ------------------------------------------------------------------ fundo
func _aplicar_fundo() -> void:
	match fundo:
		"claro": chao.texture = _textura_lisa(Color(0.96, 0.94, 0.88))
		"escuro": chao.texture = _textura_lisa(Color(0.12, 0.11, 0.14))
		_: chao.texture = textura_terreno if textura_terreno else _grama_de_teste()
	_reposicionar()


func _textura_lisa(c: Color) -> Texture2D:
	var img := Image.create_empty(8, 8, false, Image.FORMAT_RGBA8)
	img.fill(c)
	return ImageTexture.create_from_image(img)


func _grama_de_teste() -> Texture2D:
	# chao provisorio em pixel 2x2 (como o chao do jogo); troque pela textura real
	var r := RandomNumberGenerator.new()
	r.seed = 7
	var img := Image.create_empty(96, 96, false, Image.FORMAT_RGBA8)
	img.fill(Color8(104, 168, 72))
	for i in 160:
		var x := r.randi_range(0, 47) * 2
		var y := r.randi_range(0, 47) * 2
		img.fill_rect(Rect2i(x, y, 2, 2), Color8(84, 146, 60) if r.randf() < 0.6 else Color8(128, 188, 88))
	return ImageTexture.create_from_image(img)


func _reposicionar() -> void:
	var tam := get_viewport_rect().size
	# animais centralizados na area livre, a direita do painel
	var esq := (painel.position.x + painel.size.x + 16.0) if painel else 0.0
	var cx := esq + (tam.x - esq) * 0.5
	zoom_efetivo = zoom
	if comparar and not dados.is_empty():
		# no modo comparar, reduz o zoom ate os 5 caberem na area livre
		var total := 0.0
		for e in ESPECIES:
			if dados.has(e): total += float(dados[e]["celula"][0])
		zoom_efetivo = clampf(floorf((tam.x - esq - 16.0) / total), 1.0, zoom)
	mundo.position = Vector2(cx, tam.y * 0.62)
	mundo.scale = Vector2(zoom_efetivo, zoom_efetivo)
	chao.region_rect = Rect2(_scroll, tam / zoom_efetivo + Vector2(4, 4))
	chao.position = Vector2(tam.x * 0.5 - cx, -tam.y * 0.12) / zoom_efetivo
	if marcas: marcas.queue_redraw()


# ------------------------------------------------------------------ UI
func _lista_acoes(e: String) -> Array:
	var r := []
	for n in dados[e]["animacoes"]:
		if not String(n).begins_with("walk_") and n != "idle_blink":
			r.append(n)
	return r


func _preencher_listas() -> void:
	var e: String = animais[0].get_meta("especie") if animais.size() > 0 else especie
	ui_anim.clear()
	var nomes: Array = dados[e]["animacoes"].keys()
	for n in nomes:
		ui_anim.add_item(n)
	var i := nomes.find(anim_escolhida)
	if i < 0:
		anim_escolhida = nomes[0]
		i = 0
	ui_anim.select(i)
	ui_acao.clear()
	for n in _lista_acoes(e):
		ui_acao.add_item(n)
	if ui_acao.item_count > 0:
		ui_acao.select(0)
		acao_escolhida = ui_acao.get_item_text(0)


func _atualizar_info() -> void:
	if ui_info == null or animais.is_empty():
		return
	var s := animais[0]
	var e: String = s.get_meta("especie")
	var a: Dictionary = dados[e]["animacoes"].get(String(s.animation), {})
	var n := s.sprite_frames.get_frame_count(s.animation)
	var dur := s.sprite_frames.get_frame_duration(s.animation, s.frame)
	var txt := "%s  ·  %s  ·  quadro %d/%d  ·  %.2f s%s" % [
		e, s.animation, s.frame + 1, n, dur, "" if s.is_playing() else "  (pausado)"]
	var al: Array = a.get("alertas", [])
	if al.size() > 0:
		txt += "\n⚠ " + "\n⚠ ".join(PackedStringArray(al.slice(0, 3)))
	ui_info.text = txt


func _montar_ui() -> void:
	var camada := CanvasLayer.new()
	add_child(camada)
	painel = PanelContainer.new()
	painel.position = Vector2(8, 8)
	painel.resized.connect(_reposicionar)
	camada.add_child(painel)
	var col := VBoxContainer.new()
	painel.add_child(col)

	ui_especie = OptionButton.new()
	for e in ESPECIES:
		if dados.has(e): ui_especie.add_item(e)
	ui_especie.add_item("Comparar os 5")
	ui_especie.item_selected.connect(func(i):
		comparar = ui_especie.get_item_text(i) == "Comparar os 5"
		if not comparar: especie = ui_especie.get_item_text(i)
		_recriar_animais())
	col.add_child(_linha("Animal", ui_especie))

	ui_anim = OptionButton.new()
	ui_anim.item_selected.connect(func(i):
		direcao = ui_anim.get_item_text(i).trim_prefix("walk_") if ui_anim.get_item_text(i).begins_with("walk_") else direcao
		_tocar(ui_anim.get_item_text(i), true))
	col.add_child(_linha("Animação", ui_anim))

	ui_acao = OptionButton.new()
	ui_acao.item_selected.connect(func(i): acao_escolhida = ui_acao.get_item_text(i))
	var bt_acao := Button.new()
	bt_acao.text = "Tocar (E)"
	bt_acao.pressed.connect(_tocar_acao)
	col.add_child(_linha("Ação", ui_acao, bt_acao))

	var ctr := HBoxContainer.new()
	for par in [["◀", func(): _passo(-1)], ["⏯", _alternar_pausa], ["▶", func(): _passo(1)], ["⟲", func(): _tocar(anim_escolhida, true)]]:
		var b := Button.new()
		b.text = par[0]
		b.custom_minimum_size = Vector2(40, 0)
		b.pressed.connect(par[1])
		ctr.add_child(b)
	col.add_child(ctr)

	ui_vel = _slider(0.25, 2.0, 0.05, 1.0)
	var vel_txt := Label.new()
	vel_txt.text = "1.00×"
	ui_vel.value_changed.connect(func(v):
		vel_txt.text = "%.2f×" % v
		for s in animais: s.speed_scale = v)
	col.add_child(_linha("Velocidade", ui_vel, vel_txt))

	var ui_zoom := _slider(1, 8, 1, zoom)
	ui_zoom.value_changed.connect(func(v):
		zoom = v
		_reposicionar())
	col.add_child(_linha("Zoom", ui_zoom))

	ui_chao = _slider(0, 120, 1, 0)
	ui_chao_txt = Label.new()
	ui_chao_txt.text = "parado"
	ui_chao.value_changed.connect(func(v):
		chao_px_s = v
		ui_chao_txt.text = "parado" if v == 0 else "%d px/s" % v)
	col.add_child(_linha("Chão andando", ui_chao, ui_chao_txt))

	var ui_fundo := OptionButton.new()
	for f in ["terreno", "claro", "escuro"]:
		ui_fundo.add_item(f)
	ui_fundo.item_selected.connect(func(i):
		fundo = ui_fundo.get_item_text(i)
		_aplicar_fundo())
	col.add_child(_linha("Fundo", ui_fundo))

	col.add_child(_check("Mostrar pivot e caixa", true, _ao_marcar_pivot))
	col.add_child(_check("Modo natural (pausas e ações aleatórias)", false, _ao_marcar_natural))
	col.add_child(_check("Espelhar ações para a esquerda (teste)", false, _ao_marcar_espelhar))

	ui_info = Label.new()
	ui_info.custom_minimum_size = Vector2(330, 0)
	ui_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(ui_info)
	var ajuda := Label.new()
	ajuda.text = "Setas/WASD: andar · E: ação\nEspaço: pausar · , e . : quadro a quadro"
	ajuda.modulate = Color(1, 1, 1, 0.7)
	col.add_child(ajuda)


func _check(texto: String, valor: bool, acao: Callable) -> CheckBox:
	var c := CheckBox.new()
	c.text = texto
	c.button_pressed = valor
	c.toggled.connect(acao)
	return c


func _ao_marcar_pivot(b: bool) -> void:
	mostrar_pivot = b


func _ao_marcar_natural(b: bool) -> void:
	modo_natural = b
	tempo_ate_acao = 3.0


func _ao_marcar_espelhar(b: bool) -> void:
	espelhar_acoes = b
	if not andando:
		_parado_na_direcao()


func _linha(rotulo: String, a: Control, b: Control = null) -> HBoxContainer:
	var h := HBoxContainer.new()
	var l := Label.new()
	l.text = rotulo
	l.custom_minimum_size = Vector2(96, 0)
	h.add_child(l)
	a.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(a)
	if b: h.add_child(b)
	return h


func _slider(mn: float, mx: float, passo: float, v: float) -> HSlider:
	var s := HSlider.new()
	s.min_value = mn
	s.max_value = mx
	s.step = passo
	s.value = v
	s.custom_minimum_size = Vector2(120, 0)
	return s
