from PIL import Image

from assistente import capas


def test_isbn_invalido_nao_busca(monkeypatch):
    monkeypatch.setattr(capas, "_open_library", lambda i: (_ for _ in ()).throw(AssertionError("não devia buscar")))
    assert capas.buscar("123") is None


def test_arquivo_local_tem_prioridade(tmp_path, monkeypatch):
    Image.new("RGB", (400, 600), "red").save(tmp_path / "9788595081512.jpg")
    monkeypatch.setattr(capas, "_open_library", lambda i: None)
    img, origem = capas.buscar("978-85-950-8151-2", tmp_path)
    assert img.size == (400, 600) and "9788595081512.jpg" in origem


def test_sem_capa_real_devolve_none(tmp_path, monkeypatch):
    monkeypatch.setattr(capas, "_open_library", lambda i: None)
    monkeypatch.setattr(capas, "_google_books", lambda i: None)
    assert capas.buscar("9788595081512", tmp_path) is None
