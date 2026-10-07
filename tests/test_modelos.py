from assistente.modelos import LIMITE_LEGENDA_INSTAGRAM, montar_legenda, normalizar_hashtag


def test_normalizar_hashtag():
    assert normalizar_hashtag("livros") == "#livros"
    assert normalizar_hashtag("#Ficção Científica") == "#FicçãoCientífica"
    assert normalizar_hashtag("  # ") == ""


def test_legenda_junta_hashtags_sem_repetir(post):
    legenda = montar_legenda(post, hashtags_fixas=["#livros", "#leitura"], maximo=12)
    corpo, tags = legenda.split("\n\n")[:-1], legenda.split("\n\n")[-1]
    assert "\n\n".join(corpo) == post.legenda
    assert tags.split() == ["#livros", "#leitura", "#kafka", "#literatura"]


def test_legenda_respeita_limites_do_instagram(post):
    post.legenda = "a" * 5000
    post.hashtags = [f"tag{i}" for i in range(50)]
    legenda = montar_legenda(post, maximo=100)
    assert len(legenda) <= LIMITE_LEGENDA_INSTAGRAM
    assert legenda.count("#") == 30
