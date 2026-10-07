import shutil
from pathlib import Path

import pytest

from assistente.config import carregar
from assistente.modelos import Post, Slide

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def cfg(tmp_path):
    """Config real do projeto (com fontes e logo), mas gravando numa pasta temporária."""
    shutil.copy(RAIZ / "config.yaml", tmp_path / "config.yaml")
    shutil.copytree(RAIZ / "fontes", tmp_path / "fontes")
    shutil.copytree(RAIZ / "marca", tmp_path / "marca")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "historico.json").write_text("[]", encoding="utf-8")
    config = carregar(tmp_path / "config.yaml")
    config.dados["imagens_ia"]["provedor"] = "nenhum"
    return config


def slide(**campos) -> Slide:
    vazio = dict(rotulo="", titulo="", texto="", citacao="", autor_citacao="", diagrama_de="",
                 diagrama_para="", diagrama_legenda="", prompt_imagem="a candle on a desk")
    return Slide(**{**vazio, **campos})


@pytest.fixture
def carrossel():
    return Post(
        tema="Dicotomia do controle",
        pilar="Estoicismo e filosofia prática explicados de forma simples",
        mundo_visual="oleo_renascentista",
        isbn_capa="",
        slides=[
            slide(titulo="Você está tentando controlar o *incontrolável?*",
                  texto="Estoicismo explicado de forma simples.",
                  citacao="Não são as coisas que nos perturbam, mas a opinião que temos delas.",
                  autor_citacao="Epicteto"),
            *[slide(rotulo="Epicteto • Manual", titulo=f"Ideia {i}: algumas coisas *dependem* de você.",
                    texto="Separar o que está sob nosso controle do que não está.") for i in range(1, 5)],
            slide(rotulo="Na prática", titulo="Isso depende de *mim?*", texto="Se sim, aja.",
                  diagrama_de="Controle", diagrama_para="Paz", diagrama_legenda="Foque no que é seu"),
            slide(titulo="Salve para reler num *dia difícil.*", texto="E marque um amigo."),
        ],
        legenda="Você sabia que os estoicos treinavam a atenção?\n\nO que você tenta controlar hoje?",
        hashtags=["#estoicismo", "filosofia", "#Livros"],
        fontes=["https://plato.stanford.edu/entries/epictetus/"],
    )


@pytest.fixture
def imagem_unica():
    return Post(
        tema="Frankenstein nasceu de um desafio",
        pilar="Curiosidades literárias: bastidores de livros e autores famosos",
        mundo_visual="fotografia_noturna",
        isbn_capa="",
        slides=[slide(rotulo="Curiosidade literária",
                      titulo="Frankenstein nasceu de um *desafio* entre amigos.",
                      texto="Em 1816, Mary Shelley aceitou o desafio de escrever uma história de terror.")],
        legenda="Uma noite chuvosa mudou a literatura.\n\nVocê já leu Frankenstein?",
        hashtags=["#frankenstein"],
        fontes=["https://www.britannica.com/biography/Mary-Wollstonecraft-Shelley"],
    )
