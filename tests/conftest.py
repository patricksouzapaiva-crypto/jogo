import shutil
from pathlib import Path

import pytest

from assistente.config import carregar
from assistente.modelos import Post, Slide

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def cfg(tmp_path):
    """Config real do projeto, mas apontando para uma pasta temporária."""
    shutil.copy(RAIZ / "config.yaml", tmp_path / "config.yaml")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "historico.json").write_text("[]", encoding="utf-8")
    config = carregar(tmp_path / "config.yaml")
    config.dados["imagens_ia"]["provedor"] = "nenhum"
    return config


@pytest.fixture
def post():
    return Post(
        tema="Kafka pediu para queimar seus manuscritos",
        pilar="Vida e manias de escritores famosos",
        titulo_capa="Kafka pediu para queimarem tudo o que ele escreveu",
        subtitulo_capa="E foi graças a um amigo desobediente que hoje lemos A Metamorfose.",
        slides=[
            Slide(titulo="O pedido", texto="Antes de morrer, em 1924, Kafka pediu a Max Brod que queimasse tudo."),
            Slide(titulo="A desobediência", texto="Brod ignorou o pedido e publicou O Processo em 1925."),
            Slide(titulo="A fuga", texto="Em 1939, Brod fugiu de Praga levando uma mala com os papéis de Kafka."),
        ],
        chamada_final="Salve este post e conte: qual livro de Kafka você leria primeiro?",
        legenda="Você sabia que quase não conhecemos Kafka?\n\nQual livro dele você leria?",
        hashtags=["#kafka", "literatura", "#Livros"],
        fontes=["https://www.britannica.com/biography/Franz-Kafka"],
        prompt_imagem="An old wooden desk with handwritten manuscripts and a candle",
    )
