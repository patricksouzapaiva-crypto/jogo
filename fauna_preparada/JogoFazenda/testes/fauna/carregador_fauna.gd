## Carrega as animacoes preparadas da fauna (atlas + JSON) e monta SpriteFrames.
## Nao depende de nenhum outro script do jogo: pode ser usado pela cena de teste
## e, se fizer sentido, pelo sistema de animais que o jogo ja tem.
class_name CarregadorFauna
extends RefCounted

const PASTA_PADRAO := "res://arte/preparado/fauna"


## Le o fauna_index.json e devolve { especie: dados_do_json }.
static func carregar_tudo(pasta: String = PASTA_PADRAO) -> Dictionary:
	var indice: Variant = _ler_json(pasta.path_join("fauna_index.json"))
	var resultado := {}
	if indice == null:
		push_error("Fauna: nao achei fauna_index.json em " + pasta)
		return resultado
	for especie in indice["especies"]:
		var dados: Variant = _ler_json(pasta.path_join(indice["especies"][especie]["json"]))
		if dados == null:
			continue
		dados["_pasta"] = pasta.path_join(especie)
		resultado[especie] = dados
	return resultado


## Monta um SpriteFrames com todas as animacoes da especie.
## Cada quadro recebe a duracao em segundos (velocidade da animacao = 1 quadro/s,
## e a duracao relativa de cada quadro = segundos). Assim, pausas e gestos com
## tempos diferentes ficam exatos.
static func montar_sprite_frames(dados: Dictionary) -> SpriteFrames:
	var atlas := _carregar_textura(String(dados["_pasta"]).path_join(dados["atlas"]))
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
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


## Deslocamento para que a posicao do no seja o ponto de contato com o chao.
static func offset_do_pivot(dados: Dictionary) -> Vector2:
	return -Vector2(dados["pivot"][0], dados["pivot"][1])


static func _carregar_textura(caminho: String) -> Texture2D:
	if ResourceLoader.exists(caminho):
		var t: Texture2D = load(caminho)
		if t != null:
			return t
	# Fallback (ex.: arquivo ainda nao importado pelo editor)
	var img := Image.load_from_file(ProjectSettings.globalize_path(caminho))
	if img == null or img.is_empty():
		push_error("Fauna: nao consegui abrir " + caminho)
		return null
	return ImageTexture.create_from_image(img)


static func _ler_json(caminho: String) -> Variant:
	if not FileAccess.file_exists(caminho):
		return null
	return JSON.parse_string(FileAccess.get_file_as_string(caminho))
