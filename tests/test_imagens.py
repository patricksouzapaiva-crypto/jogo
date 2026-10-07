import pytest
from PIL import Image

from assistente import geracao_imagens, imagens

from .conftest import slide


def test_carrossel_tem_7_slides_no_formato_4x5(cfg, carrossel, tmp_path):
    caminhos = imagens.gerar(cfg, "carrossel", carrossel, tmp_path / "post")
    assert [c.name for c in caminhos] == [f"slide_{i:02d}.jpg" for i in range(1, 8)]
    for caminho in caminhos:
        with Image.open(caminho) as img:
            assert img.size == (1080, 1350) and img.format == "JPEG"


def test_imagem_unica(cfg, imagem_unica, tmp_path):
    caminhos = imagens.gerar(cfg, "imagem", imagem_unica, tmp_path / "post")
    assert len(caminhos) == 1


def test_fundo_claro_usa_texto_marinho(cfg, imagem_unica, tmp_path):
    desenhista = imagens.Desenhista(cfg)
    _, paleta = desenhista.preparar(Image.new("RGB", (1080, 1350), "#F4EEE0"), "unico")
    assert paleta.clara and paleta.titulo == cfg.visual["cor_marinho"]
    _, paleta = desenhista.preparar(Image.new("RGB", (1080, 1350), "#101820"), "unico")
    assert not paleta.clara and paleta.titulo == cfg.visual["cor_branco"]


def test_capa_com_livro_e_texto_longo(cfg, carrossel, tmp_path):
    carrossel.slides[0] = slide(rotulo="Bram Stoker • Drácula", titulo="Por que " * 20 + "*medo?*",
                                texto="Texto de apoio bem comprido. " * 10)
    capa = Image.new("RGB", (400, 600), "#AA2222")
    caminhos = imagens.gerar(cfg, "carrossel", carrossel, tmp_path / "post", capa_livro=capa)
    with Image.open(caminhos[0]) as img:
        r, g, b = img.getpixel((1080 - 72 - 100, 1350 - 200 - 200))  # meio da capa colada
        assert r > 150 and g < 60


def test_logo_original_e_obrigatorio(cfg, carrossel, tmp_path):
    cfg.dados["visual"]["logo"] = "marca/nao_existe.png"
    with pytest.raises(FileNotFoundError):
        imagens.gerar(cfg, "carrossel", carrossel, tmp_path / "post")


def test_prompt_usa_mundo_visual(cfg):
    prompt = geracao_imagens.montar_prompt(cfg, "A castle on a cliff", "xilogravura")
    assert prompt.startswith("Black and white woodcut")
    assert "A castle on a cliff" in prompt
    assert "upper half" in prompt and prompt.endswith("no logos.")


def test_recortar_para_4x5():
    img = geracao_imagens.recortar(Image.new("RGB", (1024, 1536)), 1080, 1350)
    assert img.size == (1080, 1350)


def test_ilustracao_desligada_ou_com_falha(cfg, monkeypatch):
    assert geracao_imagens.gerar_ilustracao(cfg, "a desk") is None

    def falha(*args):
        raise RuntimeError("serviço fora do ar")

    monkeypatch.setitem(geracao_imagens.PROVEDORES, "pollinations", falha)
    monkeypatch.setattr(geracao_imagens.time, "sleep", lambda s: None)
    cfg.dados["imagens_ia"]["provedor"] = "pollinations"
    assert geracao_imagens.gerar_ilustracao(cfg, "a desk") is None


class _Resp:
    status_code = 200
    headers = {"content-type": "image/jpeg"}
    content = b"img"
    text = ""

    def raise_for_status(self):
        pass


def test_pollinations_usa_api_nova_com_chave(monkeypatch):
    chamadas = []
    monkeypatch.setattr(geracao_imagens.requests, "get",
                        lambda url, params, headers, timeout: chamadas.append((url, params, headers)) or _Resp())
    monkeypatch.setenv("POLLINATIONS_TOKEN", "sk_teste")
    geracao_imagens._pollinations("a castle", {"pollinations_modelo": "zimage"}, 1080, 1350, 7)
    url, params, headers = chamadas[-1]
    assert url.startswith("https://gen.pollinations.ai/image/a%20castle")
    assert params["model"] == "zimage" and params["seed"] == 7
    assert headers["Authorization"] == "Bearer sk_teste"

    monkeypatch.delenv("POLLINATIONS_TOKEN")
    geracao_imagens._pollinations("a castle", {}, 1080, 1350, 7)
    url, params, headers = chamadas[-1]
    assert url.startswith("https://image.pollinations.ai/prompt/") and not headers


@pytest.mark.parametrize("chave", ["sk_abc…xyz", "pk_1234567890", "sk_abc...xyz"])
def test_chave_pollinations_invalida_da_mensagem_clara(chave):
    with pytest.raises(geracao_imagens.ChaveInvalida):
        geracao_imagens.validar_chave_pollinations(chave)


def test_chave_pollinations_valida():
    geracao_imagens.validar_chave_pollinations("sk_AbC123xyz")
