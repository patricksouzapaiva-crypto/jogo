from PIL import Image

from assistente import geracao_imagens, imagens
from assistente.modelos import Slide


def test_gera_capa_slides_e_final(cfg, post, tmp_path):
    caminhos = imagens.gerar(cfg, post, tmp_path / "post")
    assert [c.name for c in caminhos] == [f"slide_{i:02d}.jpg" for i in range(1, 6)]
    for caminho in caminhos:
        with Image.open(caminho) as img:
            assert img.size == (1080, 1350)
            assert img.format == "JPEG"


def test_capa_com_ilustracao(cfg, post, tmp_path):
    ilustracao = Image.new("RGB", (1080, 1350), "#336699")
    caminhos = imagens.gerar(cfg, post, tmp_path / "post", ilustracao)
    with Image.open(caminhos[0]) as capa:
        # o topo continua mostrando a ilustração, a parte de baixo é escurecida
        assert capa.getpixel((540, 20))[2] > 120
        assert sum(capa.getpixel((10, 1340))) < 120


def test_texto_longo_nao_quebra(cfg, post, tmp_path):
    post.titulo_capa = "Um título enorme " * 10
    post.slides = [Slide(titulo="Título " * 8, texto="Texto muito longo. " * 40)]
    caminhos = imagens.gerar(cfg, post, tmp_path / "post")
    assert len(caminhos) == 3


def test_recortar_para_4x5():
    img = geracao_imagens.recortar(Image.new("RGB", (1024, 1536)), 1080, 1350)
    assert img.size == (1080, 1350)


def test_ilustracao_desligada_ou_com_falha(cfg, monkeypatch):
    assert geracao_imagens.gerar_ilustracao(cfg, "a desk") is None

    def falha(*args):
        raise RuntimeError("serviço fora do ar")

    monkeypatch.setitem(geracao_imagens.PROVEDORES, "pollinations", falha)
    cfg.dados["imagens_ia"]["provedor"] = "pollinations"
    assert geracao_imagens.gerar_ilustracao(cfg, "a desk") is None
