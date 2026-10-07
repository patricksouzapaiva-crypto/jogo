from PIL import Image

from assistente import __main__ as cli
from assistente import geracao_imagens


def test_testar_imagem_gera_cena_e_slide(cfg, monkeypatch):
    monkeypatch.setattr(geracao_imagens, "gerar_ilustracao",
                        lambda cfg_, prompt, semente, tentativas: Image.new("RGB", (1080, 1350), "#223344"))
    assert cli.testar_imagem(cfg, "aquarela") == 0
    pasta = cfg.raiz / "posts" / "_teste"
    assert sorted(p.name for p in pasta.iterdir()) == ["aquarela_cena.jpg", "aquarela_slide.jpg"]


def test_testar_imagem_falha_sem_imagem(cfg):
    assert cli.testar_imagem(cfg, "aquarela") == 1   # provedor "nenhum" no teste: nada é gerado
    assert cli.testar_imagem(cfg, "inexistente") == 2
