from types import SimpleNamespace

import pytest

from assistente import ia


def resposta(stop_reason, texto="", conteudo=None):
    blocos = conteudo if conteudo is not None else [SimpleNamespace(type="text", text=texto)]
    return SimpleNamespace(
        stop_reason=stop_reason,
        stop_details=None,
        content=blocos,
        usage=SimpleNamespace(output_tokens=10),
    )


class ClienteFalso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pedidos = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.pedidos.append(kwargs)
        return self.respostas.pop(0)


def test_pesquisa_continua_apos_pause_turn(cfg, monkeypatch):
    pausa = resposta("pause_turn", conteudo=[SimpleNamespace(type="server_tool_use")])
    cliente = ClienteFalso([pausa, resposta("end_turn", "TEMA: Kafka")])
    monkeypatch.setattr(ia, "_cliente", lambda: cliente)

    assert ia.pesquisar(cfg, ["Tema antigo"], []) == "TEMA: Kafka"
    assert len(cliente.pedidos) == 2
    segundo = cliente.pedidos[1]["messages"]
    assert segundo[1] == {"role": "assistant", "content": pausa.content}
    assert "Tema antigo" in segundo[0]["content"]
    assert cliente.pedidos[0]["fallbacks"] == "default"
    assert cliente.pedidos[0]["tools"][0]["type"] == "web_search_20260209"


def test_pesquisa_recusada_gera_erro(cfg, monkeypatch):
    monkeypatch.setattr(ia, "_cliente", lambda: ClienteFalso([resposta("refusal")]))
    with pytest.raises(ia.ErroIA):
        ia.pesquisar(cfg, [], [])


def test_normalizar_corta_excesso_mantendo_slide_final(cfg, carrossel):
    carrossel.slides = carrossel.slides + carrossel.slides[1:3]  # 9 slides
    final = carrossel.slides[-1]
    carrossel.mundo_visual = "inexistente"
    post = ia._normalizar(cfg, carrossel, "carrossel", 7)
    assert len(post.slides) == 7 and post.slides[-1] is final
    assert post.mundo_visual in cfg.secao("mundos_visuais")
