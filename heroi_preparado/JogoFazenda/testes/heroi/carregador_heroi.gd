## Carrega as animacoes preparadas do heroi (atlas + JSON) e monta um SpriteFrames.
## Nao depende de nenhum outro script do jogo: serve para a cena de teste e para o
## personagem do jogo (basta trocar o SpriteFrames do AnimatedSprite2D dele).
class_name CarregadorHeroi
extends RefCounted

const PASTA_PADRAO := "res://arte/preparado/heroi"


## Le o heroi.json. Devolve {} se nao achar.
static func carregar(pasta: String = PASTA_PADRAO) -> Dictionary:
	var dados: Variant = _ler_json(pasta.path_join("heroi.json"))
	if dados == null:
		push_error("Heroi: nao achei heroi.json em " + pasta)
		return {}
	dados["_pasta"] = pasta
	return dados


## Monta um SpriteFrames com walk_down/left/right/up e idle_down/left/right/up.
## Cada quadro recebe a sua duracao em segundos (velocidade da animacao = 1),
## assim o andar fica com 75 ms por quadro e o respirar com tempos diferentes.
static func montar_sprite_frames(dados: Dictionary) -> SpriteFrames:
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	if dados.is_empty():
		return sf
	var atlas := _carregar_textura(String(dados["_pasta"]).path_join(dados["atlas"]))
	if atlas == null:
		return sf
	var w: int = dados["celula"][0]
	var h: int = dados["celula"][1]
	for nome in dados["animacoes"]:
		var a: Dictionary = dados["animacoes"][nome]
		sf.add_animation(nome)
		sf.set_animation_speed(nome, 1.0)
		sf.set_animation_loop(nome, bool(a["loop"]))
		for i in int(a["quadros"]):
			var t := AtlasTexture.new()
			t.atlas = atlas
			t.region = Rect2(i * w, int(a["linha"]) * h, w, h)
			sf.add_frame(nome, t, float(a["duracoes"][i]))
	return sf


## Prepara um AnimatedSprite2D: SpriteFrames, pixel nitido e pivo nos pes
## (a posicao do no passa a ser o ponto do chao entre os pes).
static func preparar_sprite(s: AnimatedSprite2D, dados: Dictionary) -> void:
	s.sprite_frames = montar_sprite_frames(dados)
	s.centered = false
	s.offset = offset_do_pivot(dados)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST


static func offset_do_pivot(dados: Dictionary) -> Vector2:
	return -Vector2(dados["pivot"][0], dados["pivot"][1])


## Quadro do andar por onde comecar quando sai do parado (fica mais suave).
static func quadro_inicio(dados: Dictionary, direcao: String) -> int:
	var a: Dictionary = dados["animacoes"].get("walk_" + direcao, {})
	return int(a.get("inicio", 0))


static func _carregar_textura(caminho: String) -> Texture2D:
	if ResourceLoader.exists(caminho):
		var t: Texture2D = load(caminho)
		if t != null:
			return t
	# Alternativa (ex.: arquivo ainda nao importado pelo editor)
	var img := Image.load_from_file(ProjectSettings.globalize_path(caminho))
	if img == null or img.is_empty():
		push_error("Heroi: nao consegui abrir " + caminho)
		return null
	return ImageTexture.create_from_image(img)


static func _ler_json(caminho: String) -> Variant:
	if not FileAccess.file_exists(caminho):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(caminho))
