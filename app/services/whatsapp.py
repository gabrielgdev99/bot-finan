import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)


async def enviar_mensagem(numero: str, texto: str) -> None:
    url = f"{settings.BAILEYS_SERVICE_URL}/send"
    payload = {"number": numero, "text": texto}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Mensagem enviada | numero=%s | status=%s", numero, response.status_code)
    except httpx.HTTPStatusError as e:
        logger.error("Erro ao enviar mensagem | status=%s | body=%s", e.response.status_code, e.response.text)
    except httpx.RequestError as e:
        logger.error("Falha de conexão com Baileys Service | erro=%s", e)
