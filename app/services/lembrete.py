import logging
from datetime import date, datetime, timedelta

import pytz
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lembrete import Lembrete
from app.models.template import Template

logger = logging.getLogger(__name__)
BRT = pytz.timezone("America/Sao_Paulo")


async def criar_lembrete(
    template_nome: str,
    dia_vencimento: int,
    auto: bool,
    db: AsyncSession,
) -> Lembrete | None:
    """
    Cria um novo lembrete vinculado a um template.
    Valida: template existe, dia entre 1-31.
    Retorna None se template não encontrado ou dia inválido.
    """
    if not (1 <= dia_vencimento <= 31):
        logger.warning("Dia inválido ao criar lembrete | dia=%d", dia_vencimento)
        return None

    template = await db.scalar(select(Template).where(Template.nome == template_nome))
    if not template:
        logger.warning("Template não encontrado ao criar lembrete | template=%s", template_nome)
        return None

    lembrete = Lembrete(
        template_id=template.id,
        dia_vencimento=dia_vencimento,
        auto=auto,
    )
    db.add(lembrete)
    await db.commit()
    await db.refresh(lembrete)
    logger.info("Lembrete criado | template=%s | dia=%d | auto=%s", template_nome, dia_vencimento, auto)
    return lembrete


async def remover_lembrete(template_nome: str, db: AsyncSession) -> Lembrete | None:
    """Remove um lembrete por nome de template. Retorna o lembrete removido."""
    template = await db.scalar(select(Template).where(Template.nome == template_nome))
    if not template:
        return None

    lembrete = await db.scalar(select(Lembrete).where(Lembrete.template_id == template.id))
    if not lembrete:
        return None

    await db.delete(lembrete)
    await db.commit()
    logger.info("Lembrete removido | template=%s", template_nome)
    return lembrete


async def listar_lembretes(db: AsyncSession) -> list[Lembrete]:
    """Lista todos os lembretes com template eager loaded."""
    resultado = await db.execute(
        select(Lembrete)
        .options(selectinload(Lembrete.template).selectinload(Template.subgrupo))
        .order_by(Lembrete.dia_vencimento)
    )
    return resultado.scalars().all()


async def processar_lembretes_do_dia(db: AsyncSession) -> tuple[list[Lembrete], list[Lembrete]]:
    """
    Processa lembretes no dia atual.
    Retorna (lembretes_aviso, lembretes_auto) — para enviar mensagens de aviso e confirmação.

    Lógica:
    - Manual: aviso 2 dias antes do vencimento
    - Auto: lança no próprio dia do vencimento
    """
    agora = datetime.now(BRT)
    hoje = agora.date()
    dia_hoje = hoje.day

    resultado = await db.execute(
        select(Lembrete)
        .options(selectinload(Lembrete.template).selectinload(Template.subgrupo))
    )
    lembretes = resultado.scalars().all()

    lembretes_aviso = []
    lembretes_auto = []

    for lembrete in lembretes:
        dia_vencimento = lembrete.dia_vencimento

        if lembrete.auto:
            # Auto: lança no próprio dia do vencimento
            # Deduplicação é feita pela função salvar_lancamento_de_template
            if dia_hoje == dia_vencimento:
                lembretes_auto.append(lembrete)
        else:
            # Manual: aviso 2 dias antes
            if dia_hoje + 2 == dia_vencimento:
                lembretes_aviso.append(lembrete)

    return lembretes_aviso, lembretes_auto
