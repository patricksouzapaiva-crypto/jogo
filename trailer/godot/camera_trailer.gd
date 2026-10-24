## Câmera de trailer: passeia por uma sequência de "tomadas" com movimentos suaves.
##
## Como usar:
## 1. Adicione um Camera2D com este script na cena do trailer (junto com o mapa da fazenda).
## 2. Crie nós Marker2D como filhos dele, na ordem das tomadas. Cada Marker2D é um ponto da câmera.
##    Metadados opcionais em cada Marker2D (Inspetor > Metadata):
##      zoom (float)      - aproximação da câmera nessa tomada (padrão: zoom_padrao)
##      duracao (float)   - segundos parado/passeando na tomada (padrão: duracao_padrao)
##      transicao (float) - segundos para chegar nela (0 = corte seco; padrão: transicao_padrao)
##      deriva (Vector2)  - deslocamento lento durante a tomada, dá vida à cena (padrão: Vector2.ZERO)
## 3. Grave com o Movie Maker do Godot (veja trailer/TRAILER.md). O jogo fecha sozinho no fim
##    (desmarque fechar_ao_terminar para só assistir no editor).
extends Camera2D

signal tomada_iniciada(indice: int, nome: String)
signal trailer_terminou

@export var zoom_padrao := 2.0
@export var duracao_padrao := 2.5
@export var transicao_padrao := 1.2
@export var espera_inicial := 0.5
@export var fechar_ao_terminar := true

var _tomadas: Array[Marker2D] = []
var _posicoes: Array[Vector2] = []


func _ready() -> void:
	for filho in get_children():
		if filho is Marker2D:
			_tomadas.append(filho)
	if _tomadas.is_empty():
		push_warning("camera_trailer: nenhum Marker2D filho; nada para filmar.")
		return
	# Os marcadores são filhos da câmera e se moveriam com ela: guarda as posições antes de começar.
	for tomada in _tomadas:
		_posicoes.append(tomada.global_position)
	make_current()
	global_position = _posicoes[0]
	zoom = Vector2.ONE * float(_tomadas[0].get_meta("zoom", zoom_padrao))
	_rodar.call_deferred()


func _rodar() -> void:
	await get_tree().create_timer(espera_inicial).timeout
	for i in _tomadas.size():
		var tomada := _tomadas[i]
		var alvo_zoom := Vector2.ONE * float(tomada.get_meta("zoom", zoom_padrao))
		var transicao := float(tomada.get_meta("transicao", transicao_padrao))
		var duracao := float(tomada.get_meta("duracao", duracao_padrao))
		var deriva: Vector2 = tomada.get_meta("deriva", Vector2.ZERO)

		tomada_iniciada.emit(i, tomada.name)
		if i == 0 or transicao <= 0.0:
			global_position = _posicoes[i]
			zoom = alvo_zoom
		else:
			var chegada := create_tween().set_parallel()
			chegada.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
			chegada.tween_property(self, "global_position", _posicoes[i], transicao)
			chegada.tween_property(self, "zoom", alvo_zoom, transicao)
			await chegada.finished

		var passeio := create_tween()
		passeio.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		passeio.tween_property(self, "global_position", _posicoes[i] + deriva, duracao)
		await passeio.finished

	trailer_terminou.emit()
	if fechar_ao_terminar:
		get_tree().quit()  # o Movie Maker finaliza o arquivo de vídeo ao fechar
