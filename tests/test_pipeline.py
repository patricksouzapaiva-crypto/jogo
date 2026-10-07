import json

from assistente import historico, ia, pipeline


def test_gerar_e_publicar(cfg, post, monkeypatch):
    vistos = {}

    def pesquisar(cfg_, temas_usados, pilares_usados, tema=None):
        vistos["temas_usados"] = temas_usados
        return "TEMA: Kafka\nFATOS: ..."

    monkeypatch.setattr(ia, "pesquisar", pesquisar)
    monkeypatch.setattr(ia, "redigir", lambda cfg_, dossie: post)

    pasta = pipeline.gerar(cfg)
    assert sorted(p.name for p in pasta.iterdir()) == [
        "dossie.md", "legenda.txt", "post.json",
        "slide_01.jpg", "slide_02.jpg", "slide_03.jpg", "slide_04.jpg", "slide_05.jpg",
    ]
    assert "#kafka" in (pasta / "legenda.txt").read_text(encoding="utf-8")
    assert historico.ler(cfg.arquivo_historico)[0]["status"] == "gerado"

    publicados = []

    class InstagramFalso:
        def __init__(self, **kwargs):
            pass

        def publicar(self, urls, legenda):
            publicados.append((urls, legenda))
            return {"midia_id": "m1", "permalink": "https://www.instagram.com/p/x/"}

    monkeypatch.setenv("IG_USER_ID", "123")
    monkeypatch.setenv("IG_ACCESS_TOKEN", "tok")
    monkeypatch.setattr(pipeline, "Instagram", InstagramFalso)
    monkeypatch.setattr(pipeline.hospedagem, "publicar_imagens",
                        lambda cfg_, caminhos: [f"https://host/{c.name}" for c in caminhos])

    resultado = pipeline.publicar(cfg, pasta)
    assert resultado["permalink"] == "https://www.instagram.com/p/x/"
    assert len(publicados[0][0]) == 5

    itens = historico.ler(cfg.arquivo_historico)
    assert len(itens) == 1 and itens[0]["status"] == "publicado"

    # rodar de novo não publica duas vezes
    pipeline.publicar(cfg, pasta)
    assert len(publicados) == 1

    # o próximo post recebe o tema anterior para evitar repetição
    pipeline.gerar(cfg)
    assert vistos["temas_usados"] == [post.tema]
    assert json.loads((pasta / "publicacao.json").read_text())["midia_id"] == "m1"
