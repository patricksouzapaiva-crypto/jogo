"""Publicação no Instagram pela API oficial (Instagram Graph API)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

LIMITE_CARROSSEL = 10


class ErroInstagram(RuntimeError):
    pass


class Instagram:
    def __init__(self, usuario_id: str, token: str, host: str = "https://graph.facebook.com",
                 versao: str = "v23.0", sessao: requests.Session | None = None,
                 espera: float = 5.0, tentativas: int = 36):
        self.usuario_id = usuario_id
        self.token = token
        self.base = f"{host.rstrip('/')}/{versao}"
        self.sessao = sessao or requests.Session()
        self.espera = espera
        self.tentativas = tentativas

    # ---- chamadas HTTP -------------------------------------------------------

    def _chamar(self, metodo: str, caminho: str, **params: Any) -> dict[str, Any]:
        params["access_token"] = self.token
        url = f"{self.base}/{caminho}"
        if metodo == "GET":
            r = self.sessao.get(url, params=params, timeout=60)
        else:
            r = self.sessao.post(url, data=params, timeout=60)
        try:
            dados = r.json()
        except ValueError:
            dados = {}
        if r.status_code >= 400 or "error" in dados:
            erro = dados.get("error", {})
            raise ErroInstagram(
                f"Erro da API do Instagram ({r.status_code}): "
                f"{erro.get('message', r.text)} [código {erro.get('code')}]"
            )
        return dados

    def _aguardar(self, container_id: str) -> None:
        """Espera o Instagram terminar de baixar/processar a mídia."""
        for _ in range(self.tentativas):
            status = self._chamar("GET", container_id, fields="status_code").get("status_code")
            if status in (None, "FINISHED"):
                return
            if status in ("ERROR", "EXPIRED"):
                raise ErroInstagram(f"O Instagram não conseguiu processar a mídia {container_id}: {status}")
            time.sleep(self.espera)
        raise ErroInstagram(f"Tempo esgotado esperando a mídia {container_id} ficar pronta.")

    # ---- publicação ----------------------------------------------------------

    def publicar(self, urls_imagens: list[str], legenda: str) -> dict[str, str]:
        if not urls_imagens:
            raise ErroInstagram("Nenhuma imagem para publicar.")
        if len(urls_imagens) > LIMITE_CARROSSEL:
            raise ErroInstagram(f"O carrossel aceita no máximo {LIMITE_CARROSSEL} imagens.")

        if len(urls_imagens) == 1:
            container = self._chamar("POST", f"{self.usuario_id}/media",
                                     image_url=urls_imagens[0], caption=legenda)["id"]
        else:
            filhos = []
            for url in urls_imagens:
                filho = self._chamar("POST", f"{self.usuario_id}/media",
                                     image_url=url, is_carousel_item="true")["id"]
                filhos.append(filho)
            for filho in filhos:
                self._aguardar(filho)
            container = self._chamar("POST", f"{self.usuario_id}/media", media_type="CAROUSEL",
                                     children=",".join(filhos), caption=legenda)["id"]

        self._aguardar(container)
        midia_id = self._chamar("POST", f"{self.usuario_id}/media_publish", creation_id=container)["id"]
        try:
            link = self._chamar("GET", midia_id, fields="permalink").get("permalink", "")
        except ErroInstagram:
            link = ""  # o post já foi publicado; o link é só um detalhe
        log.info("Publicado no Instagram: %s %s", midia_id, link)
        return {"midia_id": midia_id, "permalink": link}
