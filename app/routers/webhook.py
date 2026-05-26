import logging

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel

from app.core.config import settings
from app.services.parser import (
    parse_ajuda,
    parse_cancela,
    parse_lancamento,
    parse_orcamento,
    parse_relatorio_cartao,
    parse_resumo_comando,
    parse_ultimos,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


class _MessageKey(BaseModel):
    remoteJid: str
    fromMe: bool
    id: str


class _MessageContent(BaseModel):
    conversation: str | None = None
    extendedTextMessage: dict | None = None


class _MessageData(BaseModel):
    key: _MessageKey
    message: _MessageContent | None = None
    messageType: str | None = None
    pushName: str | None = None


class EvolutionWebhookPayload(BaseModel):
    event: str | None = None
    instance: str | None = None
    data: _MessageData | None = None


def _extrair_texto(data: _MessageData) -> str | None:
    if data.message is None:
        return None
    if data.message.conversation:
        return data.message.conversation
    if data.message.extendedTextMessage:
        return data.message.extendedTextMessage.get("text")
    return None


def _detectar_tipo(texto: str) -> str:
    t = texto.strip()
    if parse_ajuda(t):
        return "ajuda"
    if parse_lancamento(t) is not None:
        return "lancamento"
    if parse_orcamento(t) is not None:
        return "orcamento"
    if parse_relatorio_cartao(t) is not None:
        return "cartao"
    if parse_resumo_comando(t) is not None:
        return "resumo_comando"
    if parse_ultimos(t) is not None:
        return "ultimos"
    if parse_cancela(t) is not None:
        return "cancela"
    return "desconhecido"


@router.post("/whatsapp")
async def receber_mensagem(
    payload: EvolutionWebhookPayload,
    background_tasks: BackgroundTasks,
):
    if payload.event not in ("messages.upsert", "MESSAGES_UPSERT"):
        return {"status": "ignored", "reason": "event_not_relevant"}

    data = payload.data
    if data is None:
        return {"status": "ignored", "reason": "no_data"}

    logger.info("DEBUG grupo=%s fromMe=%s", data.key.remoteJid, data.key.fromMe)

    if data.key.fromMe:
        return {"status": "ignored", "reason": "own_message"}

    if settings.WHATSAPP_GROUP_ID and data.key.remoteJid != settings.WHATSAPP_GROUP_ID:
        return {"status": "ignored", "reason": "wrong_group"}

    texto = _extrair_texto(data)
    if not texto or not texto.strip():
        return {"status": "ignored", "reason": "no_text"}

    tipo = _detectar_tipo(texto)

    from app.services.mensagem import processar_mensagem  # importação local para evitar ciclo
    background_tasks.add_task(processar_mensagem, texto, tipo, data.key.remoteJid)

    logger.info("Mensagem recebida | tipo=%s | grupo=%s", tipo, data.key.remoteJid)
    return {"status": "ok"}
