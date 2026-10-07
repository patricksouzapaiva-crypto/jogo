"""Desenha os slides no layout fixo da marca (Guia de Marca, seção 3).

Etiqueta pequena no topo esquerdo · título + texto de apoio na metade superior, sobre zona
de contraste · cena na metade inferior · numeração "n/7" no canto inferior direito · logo
(sempre o arquivo original) no canto inferior esquerdo.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

from .config import Config
from .modelos import Post, Slide, sem_marcacao, trechos_destacados

MARGEM = 72
LOGO = 124

FONTES_SISTEMA = {
    "titulo": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "rotulo": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    "texto": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"],
}


@lru_cache(maxsize=None)
def _carregar_fonte(caminho: str, tamanho: int):
    return ImageFont.truetype(caminho, tamanho)


def tipos_dos_slides(formato: str, quantidade: int) -> list[str]:
    if formato == "imagem":
        return ["unico"] * quantidade
    if quantidade == 1:
        return ["capa"]
    return ["capa"] + ["conteudo"] * (quantidade - 2) + ["final"]


class Paleta:
    def __init__(self, clara: bool, marinho: str, branco: str, cinza: str):
        self.clara = clara
        if clara:  # fundos claros (aquarela, vetor, colagem...): texto azul-marinho
            self.titulo, self.texto, self.suave = marinho, marinho, "#56637A"
        else:
            self.titulo, self.texto, self.suave = branco, branco, cinza


class Desenhista:
    def __init__(self, cfg: Config):
        v = cfg.visual
        self.cfg = cfg
        self.L = int(v.get("largura", 1080))
        self.A = int(v.get("altura", 1350))
        self.marinho = v.get("cor_marinho", "#0F2747")
        self.coral = v.get("cor_coral", "#E63946")
        self.branco = v.get("cor_branco", "#F7F3EB")
        self.cinza = v.get("cor_cinza", "#A7B0BE")
        self.chamada_capa = v.get("chamada_capa", "ARRASTE PARA ENTENDER")
        self.assinatura = cfg.perfil.get("assinatura", "")
        self.arroba = cfg.perfil.get("arroba", "")
        self.caminhos_fonte = {tipo: self._resolver(v.get(f"fonte_{tipo}", "")) for tipo in FONTES_SISTEMA}
        self.logo = self._carregar_logo(self._resolver(v.get("logo", "")))

    def _resolver(self, caminho: str) -> str:
        if not caminho:
            return ""
        p = Path(caminho)
        return str(p if p.is_absolute() else self.cfg.raiz / p)

    def fonte(self, tipo: str, tamanho: int):
        for caminho in (self.caminhos_fonte.get(tipo, ""), *FONTES_SISTEMA[tipo]):
            if caminho and Path(caminho).exists():
                return _carregar_fonte(caminho, tamanho)
        return ImageFont.load_default(size=tamanho)

    @staticmethod
    def _carregar_logo(caminho: str) -> Image.Image:
        # Regra da marca: sempre o arquivo original; nunca redesenhar nem substituir.
        if not caminho or not Path(caminho).exists():
            raise FileNotFoundError(
                f"Logo não encontrado em '{caminho}'. Coloque o arquivo original e ajuste 'visual.logo'."
            )
        return Image.open(caminho).convert("RGBA")

    # ---- texto ---------------------------------------------------------------------

    @staticmethod
    def _palavra(palavra) -> str:
        return "".join(texto for texto, _ in palavra)

    def _quebrar(self, d, palavras, fonte, largura: int):
        espaco = d.textlength(" ", font=fonte)
        linhas, atual, larg_atual = [], [], 0.0
        for palavra in palavras:
            larg = d.textlength(self._palavra(palavra), font=fonte)
            extra = larg if not atual else espaco + larg
            if atual and larg_atual + extra > largura:
                linhas.append(atual)
                atual, larg_atual = [palavra], larg
            else:
                atual.append(palavra)
                larg_atual += extra
        if atual:
            linhas.append(atual)
        return linhas

    def _largura_linha(self, d, linha, fonte) -> float:
        return d.textlength(" ".join(self._palavra(p) for p in linha), font=fonte)

    def ajustar(self, d, texto: str, tipo: str, tamanho: int, minimo: int, largura: int,
                altura_max: int, entrelinha: float):
        """Diminui a fonte até o texto caber; devolve (fonte, linhas, altura_da_linha)."""
        palavras = trechos_destacados(texto)
        while True:
            fonte = self.fonte(tipo, tamanho)
            linhas = self._quebrar(d, palavras, fonte, largura)
            alt = int(tamanho * entrelinha)
            cabe_largura = all(self._largura_linha(d, l, fonte) <= largura * 1.02 for l in linhas)
            if (len(linhas) * alt <= altura_max and cabe_largura) or tamanho <= minimo:
                return fonte, linhas, alt
            tamanho -= 2

    @staticmethod
    def altura(bloco) -> int:
        return len(bloco[1]) * bloco[2]

    def escrever(self, d, x: int, y: int, bloco, cor: str) -> int:
        fonte, linhas, alt = bloco
        espaco = d.textlength(" ", font=fonte)
        for linha in linhas:
            cx = x
            for palavra in linha:
                for pedaco, destaque in palavra:
                    d.text((cx, y), pedaco, font=fonte, fill=self.coral if destaque else cor)
                    cx += d.textlength(pedaco, font=fonte)
                cx += espaco
            y += alt
        return y

    def espacado(self, d, x: float, y: int, texto: str, fonte, cor: str, espaco: int) -> float:
        """Texto com letras espaçadas (etiquetas). Devolve a largura."""
        for c in texto:
            d.text((x, y), c, font=fonte, fill=cor)
            x += d.textlength(c, font=fonte) + espaco
        return x

    def largura_espacado(self, d, texto: str, fonte, espaco: int) -> float:
        return sum(d.textlength(c, font=fonte) for c in texto) + espaco * (len(texto) - 1)

    # ---- fundo -----------------------------------------------------------------------

    def _fundo_liso(self) -> Image.Image:
        topo, base = (24, 52, 92), (7, 18, 34)
        grad = Image.new("RGB", (1, self.A))
        for y in range(self.A):
            t = y / (self.A - 1)
            grad.putpixel((0, y), tuple(int(topo[i] * (1 - t) + base[i] * t) for i in range(3)))
        return grad.resize((self.L, self.A))

    def _sombra_vertical(self, img, cor, alfa: int, fim: float, de_baixo: bool = False):
        coluna = Image.new("L", (1, self.A))
        limite = int(self.A * fim)
        for y in range(self.A):
            pos = (self.A - 1 - y) if de_baixo else y
            coluna.putpixel((0, y), int(alfa * max(0.0, 1 - pos / limite)) if pos < limite else 0)
        return Image.composite(Image.new("RGB", img.size, cor), img, coluna.resize(img.size))

    def preparar(self, fundo: Image.Image | None, tipo: str) -> tuple[Image.Image, Paleta]:
        img = (fundo or self._fundo_liso()).convert("RGB").resize((self.L, self.A))
        topo = img.crop((0, 0, self.L, int(self.A * 0.5))).convert("L")
        clara = fundo is not None and ImageStat.Stat(topo).mean[0] > 150
        if clara:
            img = self._sombra_vertical(img, self.branco, 225, 0.6)
        else:
            img = self._sombra_vertical(img, "#081527", 235 if tipo == "final" else 215, 0.66)
            img = self._sombra_vertical(img, "#081527", 170, 0.24, de_baixo=True)
        return img, Paleta(clara, self.marinho, self.branco, self.cinza)

    # ---- elementos fixos -----------------------------------------------------------

    def colar_logo(self, img: Image.Image) -> None:
        logo = self.logo.resize((LOGO, LOGO), Image.LANCZOS)
        img.paste(logo, (44, self.A - 44 - LOGO), logo)

    def contador(self, d, pagina: int, total: int, paleta: Paleta) -> None:
        texto = f"{pagina}/{total}"
        fonte = self.fonte("texto", 30)
        d.text((self.L - MARGEM - d.textlength(texto, font=fonte), self.A - 100), texto,
               font=fonte, fill=paleta.suave)

    def etiqueta(self, d, y: int, texto: str) -> int:
        if not texto:
            return y
        self.espacado(d, MARGEM, y, texto.upper(), self.fonte("rotulo", 25), self.coral, 6)
        return y + 52

    def diagrama(self, d, y: int, slide: Slide, paleta: Paleta) -> int:
        fonte = self.fonte("rotulo", 32)
        de, para = slide.diagrama_de.upper(), slide.diagrama_para.upper()
        seta = 170
        x = MARGEM
        d.text((x, y), de, font=fonte, fill=paleta.titulo)
        x += d.textlength(de, font=fonte) + 30
        meio = y + 20
        d.line((x, meio, x + seta, meio), fill=self.coral, width=5)
        d.polygon([(x + seta + 4, meio), (x + seta - 18, meio - 13), (x + seta - 18, meio + 13)], fill=self.coral)
        d.text((x + seta + 30, y), para, font=fonte, fill=paleta.titulo)
        y += 54
        if slide.diagrama_legenda:
            d.text((MARGEM, y), slide.diagrama_legenda, font=self.fonte("texto", 28), fill=paleta.suave)
            y += 40
        return y

    def botao_arraste(self, d, paleta: Paleta) -> None:
        fonte = self.fonte("rotulo", 18)
        texto = self.chamada_capa.upper()
        altura = 60
        larg = self.largura_espacado(d, texto, fonte, 5) + 60 + altura
        x1 = (self.L - larg) / 2
        y1 = self.A - 44 - LOGO / 2 - altura / 2
        d.rounded_rectangle((x1, y1, x1 + larg, y1 + altura), radius=altura // 2, outline=self.coral, width=2)
        self.espacado(d, x1 + 30, y1 + 20, texto, fonte, paleta.titulo, 5)
        cx = x1 + larg - altura
        d.ellipse((cx, y1, cx + altura, y1 + altura), fill=self.coral)
        my, mx = y1 + altura / 2, cx + altura / 2
        for linha in ((mx - 13, my, mx + 11, my), (mx + 2, my - 9, mx + 12, my), (mx + 2, my + 9, mx + 12, my)):
            d.line(linha, fill=self.branco, width=4)

    def colar_capa_livro(self, img: Image.Image, capa: Image.Image, base: int) -> None:
        """Capa real do livro no canto direito, com sombra suave (sem alterar o design dela)."""
        altura = 440
        largura = round(capa.width * altura / capa.height)
        capa = capa.resize((largura, altura), Image.LANCZOS)
        x, y = self.L - MARGEM - largura, base - altura
        sombra = Image.new("L", img.size, 0)
        ImageDraw.Draw(sombra).rectangle((x + 14, y + 18, x + largura + 14, y + altura + 18), fill=170)
        sombra = sombra.filter(ImageFilter.GaussianBlur(16))
        img.paste(Image.new("RGB", img.size, "#000000"), (0, 0), sombra)
        img.paste(capa, (x, y))

    # ---- slides ------------------------------------------------------------------------

    def slide(self, tipo: str, slide: Slide, fundo, pagina: int, total: int,
              capa_livro: Image.Image | None = None) -> Image.Image:
        img, paleta = self.preparar(fundo, tipo)
        d = ImageDraw.Draw(img)
        largura = self.L - 2 * MARGEM - 30
        y = self.etiqueta(d, 92, slide.rotulo)

        # limite inferior do bloco de texto: metade superior, ou acima da capa do livro
        limite = 760 if capa_livro is not None else int(self.A * 0.62)
        if tipo == "capa" and slide.citacao:
            citacao = self.ajustar(d, f"“{sem_marcacao(slide.citacao)}”", "texto", 34, 26, largura - 120, 150, 1.3)
            y = self.escrever(d, MARGEM, y, citacao, paleta.texto)
            if slide.autor_citacao:
                self.espacado(d, MARGEM, y + 10, slide.autor_citacao.upper(), self.fonte("texto", 20), paleta.suave, 6)
                y += 44
            y += 30

        apoio = None
        if slide.texto:
            apoio = self.ajustar(d, slide.texto, "texto", 38 if tipo == "capa" else 35, 26,
                                 largura - 90, 200, 1.3)
        extra = (self.altura(apoio) + 24 if apoio else 0) + (100 if slide.diagrama_de else 0)
        grande = tipo in ("capa", "final")
        titulo = self.ajustar(d, slide.titulo, "titulo", 92 if grande else 80, 44, largura,
                              max(limite - y - extra, 120), 1.08)
        y = self.escrever(d, MARGEM, y, titulo, paleta.titulo)
        if apoio:
            y = self.escrever(d, MARGEM, y + 24, apoio, paleta.texto)
        if slide.diagrama_de and slide.diagrama_para:
            y = self.diagrama(d, y + 40, slide, paleta)

        if tipo == "final" and self.assinatura:
            d.line((MARGEM, y + 36, MARGEM + 64, y + 36), fill=self.coral, width=5)
            d.text((MARGEM, y + 60), self.assinatura, font=self.fonte("texto", 28), fill=paleta.suave)
        if capa_livro is not None:
            self.colar_capa_livro(img, capa_livro, self.A - 200)
        if tipo == "capa":
            self.botao_arraste(d, paleta)

        self.colar_logo(img)
        if tipo != "unico":
            self.contador(d, pagina, total, paleta)
        return img


def gerar(cfg: Config, formato: str, post: Post, pasta: Path,
          fundos: list[Image.Image | None] | None = None,
          capa_livro: Image.Image | None = None) -> list[Path]:
    """Cria os JPEGs do post na pasta indicada e devolve os caminhos em ordem."""
    pasta.mkdir(parents=True, exist_ok=True)
    desenhista = Desenhista(cfg)
    total = len(post.slides)
    fundos = list(fundos or []) + [None] * total
    tipos = tipos_dos_slides(formato, total)

    caminhos = []
    for i, (slide, tipo) in enumerate(zip(post.slides, tipos)):
        img = desenhista.slide(tipo, slide, fundos[i], i + 1, total,
                               capa_livro if tipo == "capa" else None)
        caminho = pasta / f"slide_{i + 1:02d}.jpg"
        img.save(caminho, "JPEG", quality=92, optimize=True)
        caminhos.append(caminho)
    return caminhos
