from assistente.modelos import (
    LIMITE_LEGENDA_INSTAGRAM, montar_legenda, normalizar_hashtag, sem_marcacao, trechos_destacados,
)


def test_normalizar_hashtag():
    assert normalizar_hashtag("livros") == "#livros"
    assert normalizar_hashtag("#Ficção Científica") == "#FicçãoCientífica"
    assert normalizar_hashtag("  # ") == ""


def test_trechos_destacados_mantem_pontuacao_grudada():
    palavras = trechos_destacados("Seus *julgamentos*, escolhas. Dez anos depois, ele *voltou.*")
    textos = ["".join(t for t, _ in p) for p in palavras]
    assert textos == ["Seus", "julgamentos,", "escolhas.", "Dez", "anos", "depois,", "ele", "voltou."]
    assert palavras[1] == [("julgamentos", True), (",", False)]
    assert palavras[-1] == [("voltou.", True)]
    assert sem_marcacao("ele *voltou.*") == "ele voltou."


def test_legenda_junta_hashtags_sem_repetir(carrossel):
    legenda = montar_legenda(carrossel, hashtags_fixas=["#mapadasideias", "#livros"], maximo=6)
    corpo, tags = legenda.rsplit("\n\n", 1)
    assert corpo == carrossel.legenda
    assert tags.split() == ["#mapadasideias", "#livros", "#estoicismo", "#filosofia"]


def test_legenda_respeita_limites_do_instagram(carrossel):
    carrossel.legenda = "a" * 5000
    carrossel.hashtags = [f"tag{i}" for i in range(50)]
    legenda = montar_legenda(carrossel, maximo=100)
    assert len(legenda) <= LIMITE_LEGENDA_INSTAGRAM
    assert legenda.count("#") == 30
