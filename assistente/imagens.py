"""Gera as imagens do carrossel (capa, slides de conteúdo e slide final) com o Pillow."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import Config
from .modelos import Post

FONTES_TITULO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/Library/Fonts/Georgia Bold.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
]
FONTES_TEXTO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/Library/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/georgia.ttf",
]

MARGEM = 96


@lru_cache(maxsize=None)
def _fonte(caminho_preferido: str, candidatos: tuple[str, ...], tamanho: int) -> ImageFont.FreeTypeFont:
    for caminho in (caminho_preferido, *candidatos):
        if caminho and Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default(size=tamanho)


class Desenhista:
    def __init__(self, cfg: Config):
        v = cfg.visual
        self.largura = int(v.get("largura", 1080))
        self.altura = int(v.get("altura", 1350))
        self.fundo = v.get("cor_fundo", "#F4EDE1")
        self.tinta = v.get("cor_texto", "#2B2622")
        self.destaque = v.get("cor_destaque", "#8C3B2E")
        self.suave = v.get("cor_suave", "#7A6E64")
        self.fonte_titulo_cfg = self._resolver(cfg, v.get("fonte_titulo", ""))
        self.fonte_texto_cfg = self._resolver(cfg, v.get("fonte_texto", ""))
        self.arroba = cfg.perfil.get("arroba", "")
        self.nome = cfg.perfil.get("nome", "")

    @staticmethod
    def _resolver(cfg: Config, caminho: str) -> str:
        if not caminho:
            return ""
        p = Path(caminho)
        return str(p if p.is_absolute() else cfg.raiz / p)

    def titulo(self, tamanho: int):
        return _fonte(self.fonte_titulo_cfg, tuple(FONTES_TITULO), tamanho)

    def texto(self, tamanho: int):
        return _fonte(self.fonte_texto_cfg, tuple(FONTES_TEXTO), tamanho)

    # ---- utilidades de texto -------------------------------------------------

    @staticmethod
    def quebrar(desenho: ImageDraw.ImageDraw, texto: str, fonte, largura_max: int) -> list[str]:
        linhas: list[str] = []
        for paragrafo in texto.split("\n"):
            atual = ""
            for palavra in paragrafo.split():
                teste = f"{atual} {palavra}".strip()
                if desenho.textlength(teste, font=fonte) <= largura_max or not atual:
                    atual = teste
                else:
                    linhas.append(atual)
                    atual = palavra
            linhas.append(atual)
        return linhas

    def ajustar(self, desenho, texto: str, criar_fonte, tamanho: int, minimo: int,
                largura_max: int, altura_max: int, entrelinha: float):
        """Diminui a fonte até o texto caber na área disponível."""
        while True:
            fonte = criar_fonte(tamanho)
            linhas = self.quebrar(desenho, texto, fonte, largura_max)
            altura_linha = int(tamanho * entrelinha)
            if len(linhas) * altura_linha <= altura_max or tamanho <= minimo:
                return fonte, linhas, altura_linha
            tamanho -= 2

    def escrever(self, desenho, xy, linhas, fonte, altura_linha, cor) -> int:
        x, y = xy
        for linha in linhas:
            desenho.text((x, y), linha, font=fonte, fill=cor)
            y += altura_linha
        return y

    # ---- elementos comuns ----------------------------------------------------

    def _base(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("RGB", (self.largura, self.altura), self.fundo)
        desenho = ImageDraw.Draw(img)
        # moldura fina, lembrando a página de um livro
        desenho.rectangle(
            (40, 40, self.largura - 40, self.altura - 40), outline=self.suave, width=2
        )
        return img, desenho

    def _rodape(self, desenho, pagina: int, total: int, cor: str | None = None) -> None:
        fonte = self.texto(30)
        cor = cor or self.suave
        y = self.altura - MARGEM - 10
        desenho.text((MARGEM, y), self.arroba, font=fonte, fill=cor)
        marcador = f"{pagina}/{total}"
        largura = desenho.textlength(marcador, font=fonte)
        desenho.text((self.largura - MARGEM - largura, y), marcador, font=fonte, fill=cor)

    # ---- slides --------------------------------------------------------------

    def capa(self, post: Post, total: int, ilustracao: Image.Image | None = None) -> Image.Image:
        if ilustracao is not None:
            return self._capa_ilustrada(post, total, ilustracao)
        img, d = self._base()
        largura_util = self.largura - 2 * MARGEM

        d.text((MARGEM, MARGEM + 20), self.nome.upper(), font=self.texto(30), fill=self.destaque)
        d.line((MARGEM, MARGEM + 80, MARGEM + 120, MARGEM + 80), fill=self.destaque, width=4)

        fonte_t, linhas_t, alt_t = self.ajustar(
            d, post.titulo_capa, self.titulo, 104, 56, largura_util, 620, 1.15
        )
        fonte_s, linhas_s, alt_s = self.ajustar(
            d, post.subtitulo_capa, self.texto, 44, 30, largura_util, 260, 1.35
        )
        altura_bloco = len(linhas_t) * alt_t + 50 + len(linhas_s) * alt_s
        y = max(MARGEM + 140, (self.altura - altura_bloco) // 2)
        y = self.escrever(d, (MARGEM, y), linhas_t, fonte_t, alt_t, self.tinta)
        y += 50
        self.escrever(d, (MARGEM, y), linhas_s, fonte_s, alt_s, self.suave)

        self._seta(d, self.destaque)
        self._rodape(d, 1, total)
        return img

    def _capa_ilustrada(self, post: Post, total: int, ilustracao: Image.Image) -> Image.Image:
        """Ilustração em tela cheia com um degradê escuro embaixo para o texto ficar legível."""
        img = ilustracao.convert("RGB").resize((self.largura, self.altura))
        sombra = Image.new("L", (1, self.altura))
        inicio = int(self.altura * 0.35)
        for y in range(self.altura):
            fracao = max(0.0, (y - inicio) / (self.altura - inicio))
            sombra.putpixel((0, y), int(235 * min(1.0, fracao * 1.3)))
        preto = Image.new("RGB", img.size, "#120E0B")
        img = Image.composite(preto, img, sombra.resize(img.size))

        d = ImageDraw.Draw(img)
        largura_util = self.largura - 2 * MARGEM
        branco, creme = "#FFFFFF", "#E9DFD1"

        fonte_t, linhas_t, alt_t = self.ajustar(
            d, post.titulo_capa, self.titulo, 96, 52, largura_util, 440, 1.15
        )
        fonte_s, linhas_s, alt_s = self.ajustar(
            d, post.subtitulo_capa, self.texto, 40, 28, largura_util, 200, 1.35
        )
        bloco = len(linhas_t) * alt_t + 36 + len(linhas_s) * alt_s
        y = self.altura - MARGEM - 150 - bloco
        d.text((MARGEM, y - 70), self.nome.upper(), font=self.texto(30), fill=creme)
        y = self.escrever(d, (MARGEM, y), linhas_t, fonte_t, alt_t, branco)
        y += 36
        self.escrever(d, (MARGEM, y), linhas_s, fonte_s, alt_s, creme)

        self._seta(d, creme)
        self._rodape(d, 1, total, cor=creme)
        return img

    def _seta(self, desenho, cor) -> None:
        seta = "arraste para o lado  →"
        fonte = self.texto(32)
        largura = desenho.textlength(seta, font=fonte)
        desenho.text((self.largura - MARGEM - largura, self.altura - MARGEM - 80), seta,
                     font=fonte, fill=cor)

    def conteudo(self, numero: int, titulo: str, texto: str, pagina: int, total: int) -> Image.Image:
        img, d = self._base()
        largura_util = self.largura - 2 * MARGEM

        d.text((MARGEM, MARGEM + 10), f"{numero:02d}", font=self.titulo(120), fill=self.destaque)
        y = MARGEM + 190

        fonte_t, linhas_t, alt_t = self.ajustar(
            d, titulo, self.titulo, 64, 40, largura_util, 240, 1.2
        )
        y = self.escrever(d, (MARGEM, y), linhas_t, fonte_t, alt_t, self.tinta)
        y += 20
        d.line((MARGEM, y, MARGEM + 120, y), fill=self.destaque, width=4)
        y += 50

        espaco = self.altura - y - MARGEM - 80
        fonte_c, linhas_c, alt_c = self.ajustar(
            d, texto, self.texto, 52, 28, largura_util, espaco, 1.45
        )
        self.escrever(d, (MARGEM, y), linhas_c, fonte_c, alt_c, self.tinta)
        self._rodape(d, pagina, total)
        return img

    def final(self, post: Post, total: int) -> Image.Image:
        img, d = self._base()
        largura_util = self.largura - 2 * MARGEM
        fonte, linhas, alt = self.ajustar(
            d, post.chamada_final, self.titulo, 72, 40, largura_util, 600, 1.25
        )
        bloco = len(linhas) * alt
        y = (self.altura - bloco) // 2 - 60
        y = self.escrever(d, (MARGEM, y), linhas, fonte, alt, self.tinta)
        y += 60
        d.line((MARGEM, y, MARGEM + 120, y), fill=self.destaque, width=4)
        d.text((MARGEM, y + 40), f"Siga {self.arroba}", font=self.titulo(48), fill=self.destaque)
        self._rodape(d, total, total)
        return img


def gerar(cfg: Config, post: Post, pasta: Path, ilustracao: Image.Image | None = None) -> list[Path]:
    """Cria os JPEGs do carrossel na pasta indicada e devolve os caminhos em ordem."""
    pasta.mkdir(parents=True, exist_ok=True)
    desenhista = Desenhista(cfg)
    total = len(post.slides) + 2

    imagens = [desenhista.capa(post, total, ilustracao)]
    for i, slide in enumerate(post.slides, start=1):
        imagens.append(desenhista.conteudo(i, slide.titulo, slide.texto, i + 1, total))
    imagens.append(desenhista.final(post, total))

    caminhos = []
    for i, img in enumerate(imagens, start=1):
        caminho = pasta / f"slide_{i:02d}.jpg"
        img.save(caminho, "JPEG", quality=92, optimize=True)
        caminhos.append(caminho)
    return caminhos
