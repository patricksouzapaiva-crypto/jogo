import pytest

from assistente.instagram import ErroInstagram, Instagram


class Resposta:
    def __init__(self, dados, status=200):
        self.dados = dados
        self.status_code = status
        self.text = str(dados)

    def json(self):
        return self.dados


class SessaoFalsa:
    """Imita a Graph API: cria containers, informa status e publica."""

    def __init__(self, erro_em=None):
        self.chamadas = []
        self.contador = 0
        self.erro_em = erro_em

    def post(self, url, data, timeout):
        self.chamadas.append(("POST", url, dict(data)))
        if self.erro_em and self.erro_em in url:
            return Resposta({"error": {"message": "token inválido", "code": 190}}, 400)
        if url.endswith("/media_publish"):
            return Resposta({"id": "midia_final"})
        self.contador += 1
        return Resposta({"id": f"c{self.contador}"})

    def get(self, url, params, timeout):
        self.chamadas.append(("GET", url, dict(params)))
        if params.get("fields") == "permalink":
            return Resposta({"permalink": "https://www.instagram.com/p/abc/"})
        return Resposta({"status_code": "FINISHED"})


def test_publica_carrossel():
    sessao = SessaoFalsa()
    ig = Instagram("123", "tok", sessao=sessao, espera=0)
    resultado = ig.publicar(["https://img/1.jpg", "https://img/2.jpg"], "legenda")

    assert resultado == {"midia_id": "midia_final", "permalink": "https://www.instagram.com/p/abc/"}
    posts = [c for c in sessao.chamadas if c[0] == "POST"]
    assert posts[0][2]["is_carousel_item"] == "true"
    assert posts[2][2]["media_type"] == "CAROUSEL"
    assert posts[2][2]["children"] == "c1,c2"
    assert posts[2][2]["caption"] == "legenda"
    assert posts[3][2]["creation_id"] == "c3"
    assert all(c[2]["access_token"] == "tok" for c in sessao.chamadas)


def test_publica_imagem_unica():
    sessao = SessaoFalsa()
    Instagram("123", "tok", sessao=sessao, espera=0).publicar(["https://img/1.jpg"], "oi")
    primeiro = sessao.chamadas[0][2]
    assert primeiro["image_url"] == "https://img/1.jpg" and primeiro["caption"] == "oi"


def test_erro_da_api_vira_excecao_clara():
    ig = Instagram("123", "tok", sessao=SessaoFalsa(erro_em="/media"), espera=0)
    with pytest.raises(ErroInstagram, match="token inválido"):
        ig.publicar(["https://img/1.jpg"], "oi")


def test_limite_de_imagens():
    ig = Instagram("123", "tok", sessao=SessaoFalsa(), espera=0)
    with pytest.raises(ErroInstagram):
        ig.publicar([f"https://img/{i}.jpg" for i in range(11)], "oi")
