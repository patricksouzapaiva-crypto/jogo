## Cena de TESTE do heroi (isolada e reversivel: apague a pasta res://testes/heroi para remover).
## Nao mexe em nenhuma regra do jogo.
##
## Teclado: setas ou WASD = andar (parado -> andar -> parado e troca de direcao)
##          Espaco = modo demonstracao (ele anda sozinho num quadrado e para entre os lados)
##          1 / 2 / 3 / 4 = zoom
extends Node2D

@export var pasta_heroi := "res://arte/preparado/heroi"
## Coloque aqui a textura do chao do jogo para testar sobre o terreno real.
@export var textura_terreno: Texture2D
@export var zoom := 4
@export var demonstracao := true

const VETOR := {"down": Vector2.DOWN, "left": Vector2.LEFT, "right": Vector2.RIGHT, "up": Vector2.UP}
## roteiro da demonstracao: [direcao ou "parado", segundos]
const ROTEIRO := [["right", 2.0], ["parado", 1.6], ["down", 1.4], ["parado", 1.6],
		["left", 2.0], ["parado", 1.6], ["up", 1.4], ["parado", 1.6]]

var dados := {}
var heroi: AnimatedSprite2D
var camera: Camera2D
var chao: Sprite2D
var info: Label
var direcao := "down"
var andando := false
var posicao := Vector2.ZERO        # em px do jogo; na tela vai arredondada (pixel sempre nitido)
var velocidade := 47.0
var _passo := 0
var _tempo_passo := 0.0


func _ready() -> void:
	dados = CarregadorHeroi.carregar(pasta_heroi)
	velocidade = float(dados.get("velocidade_andar_px_s", 47.0))
	chao = Sprite2D.new()
	chao.centered = true
	chao.region_enabled = true
	chao.region_rect = Rect2(0, 0, 4096, 4096)
	chao.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	chao.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	chao.texture = textura_terreno if textura_terreno != null else _grama()
	add_child(chao)
	heroi = AnimatedSprite2D.new()
	CarregadorHeroi.preparar_sprite(heroi, dados)
	add_child(heroi)
	camera = Camera2D.new()
	add_child(camera)
	camera.make_current()
	var camada := CanvasLayer.new()
	add_child(camada)
	info = Label.new()
	info.position = Vector2(12, 8)
	info.add_theme_color_override("font_outline_color", Color.BLACK)
	info.add_theme_constant_override("outline_size", 4)
	camada.add_child(info)
	_tocar("idle_down")
	_atualizar_tela()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE:
				demonstracao = not demonstracao
				_passo = 0
				_tempo_passo = 0.0
			KEY_1, KEY_2, KEY_3, KEY_4:
				zoom = int(event.keycode - KEY_0)


func _process(delta: float) -> void:
	var v := _entrada()
	if v == Vector2.ZERO and demonstracao:
		v = _roteiro(delta)
	if v != Vector2.ZERO:
		var nova := ("right" if v.x > 0 else "left") if v.x != 0 else ("down" if v.y > 0 else "up")
		if not andando:
			andando = true
			direcao = nova
			_tocar("walk_" + direcao, CarregadorHeroi.quadro_inicio(dados, direcao))
		elif nova != direcao:
			# troca de direcao andando: continua no mesmo ponto do passo (mesma perna na frente)
			var q := heroi.frame
			direcao = nova
			_tocar("walk_" + direcao, q)
		posicao += VETOR[direcao] * velocidade * delta
	elif andando:
		andando = false
		_tocar("idle_" + direcao, 0)
	_atualizar_tela()


func _entrada() -> Vector2:
	var v := Vector2.ZERO
	if Input.is_action_pressed("ui_right") or Input.is_physical_key_pressed(KEY_D): v.x += 1
	if Input.is_action_pressed("ui_left") or Input.is_physical_key_pressed(KEY_A): v.x -= 1
	if Input.is_action_pressed("ui_down") or Input.is_physical_key_pressed(KEY_S): v.y += 1
	if Input.is_action_pressed("ui_up") or Input.is_physical_key_pressed(KEY_W): v.y -= 1
	return v


func _roteiro(delta: float) -> Vector2:
	_tempo_passo += delta
	if _tempo_passo >= float(ROTEIRO[_passo][1]):
		_tempo_passo = 0.0
		_passo = (_passo + 1) % ROTEIRO.size()
	var etapa: String = ROTEIRO[_passo][0]
	return Vector2.ZERO if etapa == "parado" else VETOR[etapa]


func _tocar(nome: String, quadro := -1) -> void:
	if heroi.animation != StringName(nome) or not heroi.is_playing():
		heroi.play(nome)
	if quadro >= 0:
		heroi.frame = quadro % heroi.sprite_frames.get_frame_count(nome)


func _atualizar_tela() -> void:
	heroi.position = posicao.round()
	camera.position = heroi.position + Vector2(0, -32)
	camera.zoom = Vector2(zoom, zoom)
	chao.position = (heroi.position / 64.0).floor() * 64.0
	var n := heroi.sprite_frames.get_frame_count(heroi.animation) if heroi.sprite_frames.has_animation(heroi.animation) else 0
	info.text = "%s   quadro %d/%d   %.0f px/s   zoom %dx\n[setas/WASD] andar   [Espaco] demonstracao: %s   [1-4] zoom" % [
		heroi.animation, heroi.frame + 1, n, velocidade, zoom, "ligada" if demonstracao else "desligada"]


func _grama() -> Texture2D:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	img.fill(Color8(98, 150, 66))
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 140:
		var c := Color8(84, 132, 56) if rng.randf() < 0.6 else Color8(118, 170, 80)
		img.set_pixel(rng.randi_range(0, 63), rng.randi_range(0, 63), c)
	return ImageTexture.create_from_image(img)
