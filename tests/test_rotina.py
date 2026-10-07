import json

from assistente import pipeline, rotina
from assistente import __main__ as cli

PROMPT = " ".join(["word"] * 40)


def escrever(cfg, post, formato="carrossel"):
    pasta = rotina.nova_pasta(cfg, formato, post.tema)
    for slide in post.slides:
        slide.prompt_imagem = PROMPT
    dados = {"formato": formato, **post.model_dump()}
    (pasta / "post.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    (pasta / "dossie.md").write_text("TEMA: teste\nFATOS: ...", encoding="utf-8")
    return pasta


def test_briefing_traz_regras_historico_e_formato(cfg):
    texto = rotina.briefing(cfg, "carrossel")
    assert "Etapa 1 — Pesquisa" in texto and "Checklist de revisão" in texto
    assert "Nunca inventar" in texto and "7 slides" in texto
    assert '"mundo_visual"' in texto and "xilogravura" in texto


def test_post_valido_passa(cfg, carrossel):
    pasta = escrever(cfg, carrossel)
    assert rotina.validar(cfg, pasta) == []
    assert rotina.pendentes(cfg) == [pasta]


def test_validar_aponta_problemas(cfg, carrossel):
    carrossel.slides = carrossel.slides[:5]
    carrossel.mundo_visual = "inventado"
    carrossel.legenda = "Texto com #hashtag"
    pasta = escrever(cfg, carrossel)
    carrossel.slides[-1].titulo = "Arraste para o *lado"
    dados = json.loads((pasta / "post.json").read_text())
    dados["slides"][-1]["titulo"] = "Arraste para o *lado"
    (pasta / "post.json").write_text(json.dumps(dados), encoding="utf-8")
    problemas = " | ".join(rotina.validar(cfg, pasta))
    assert "7 slide" in problemas and "mundo_visual" in problemas
    assert "hashtags" in problemas and "arraste" in problemas and "asteriscos" in problemas


def test_validar_json_quebrado(cfg, tmp_path):
    (tmp_path / "post.json").write_text("{ isso não é json", encoding="utf-8")
    assert "inválido" in rotina.validar(cfg, tmp_path)[0]


def test_montar_pendentes_gera_slides_e_sai_da_fila(cfg, carrossel, imagem_unica):
    escrever(cfg, carrossel)
    escrever(cfg, imagem_unica, "imagem")
    assert cli.main(["--config", str(cfg.raiz / "config.yaml"), "montar", "--pendentes"]) == 0
    assert rotina.pendentes(cfg) == []
    pastas = sorted(cfg.pasta_posts.iterdir())
    assert len(list(pastas[0].glob("slide_*.jpg"))) + len(list(pastas[1].glob("slide_*.jpg"))) == 8
    assert all((p / "legenda.txt").exists() for p in pastas)


def test_cli_validar_devolve_erro_quando_ha_problema(cfg, carrossel, capsys):
    carrossel.fontes = []
    pasta = escrever(cfg, carrossel)
    assert cli.main(["--config", str(cfg.raiz / "config.yaml"), "validar", str(pasta)]) == 1
    assert "fontes" in capsys.readouterr().out
