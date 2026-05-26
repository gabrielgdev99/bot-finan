import hashlib
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grupo import Grupo
from app.models.lancamento import Lancamento
from app.models.subgrupo import Subgrupo
from app.schemas import LancamentoDTO, LancamentoInfo, OrcamentoDTO

logger = logging.getLogger(__name__)


async def salvar_lancamento(
    dto: LancamentoDTO,
    db: AsyncSession,
) -> Lancamento | None:
    hash_msg = _hash(dto.texto_original)

    duplicata = await db.scalar(select(Lancamento).where(Lancamento.hash_msg == hash_msg))
    if duplicata:
        logger.info("Lançamento duplicado ignorado | hash=%s", hash_msg)
        return None

    grupo = await _obter_ou_criar_grupo(dto.grupo, db)
    subgrupo = await _obter_ou_criar_subgrupo(dto.subgrupo, grupo.id, db)

    lancamento = Lancamento(
        data_gasto=dto.data_gasto,
        descricao=dto.descricao,
        valor=dto.valor,
        grupo_id=grupo.id,
        subgrupo_id=subgrupo.id,
        cartao=dto.cartao,
        data_pagamento=dto.data_pagamento,
        hash_msg=hash_msg,
    )
    db.add(lancamento)

    try:
        await db.commit()
        await db.refresh(lancamento)
        logger.info("Lançamento salvo | id=%s | grupo=%s | valor=%s", lancamento.id, dto.grupo, dto.valor)
        return lancamento
    except IntegrityError:
        await db.rollback()
        logger.warning("Conflito de hash ao salvar lançamento | hash=%s", hash_msg)
        return None


async def definir_orcamento(dto: OrcamentoDTO, db: AsyncSession) -> Subgrupo:
    grupo = await _obter_ou_criar_grupo(dto.grupo, db)
    subgrupo = await _obter_ou_criar_subgrupo(dto.subgrupo, grupo.id, db)
    subgrupo.orcamento_mensal = dto.valor
    await db.commit()
    await db.refresh(subgrupo)
    logger.info("Orçamento definido | grupo=%s | subgrupo=%s | valor=%s", dto.grupo, dto.subgrupo, dto.valor)
    return subgrupo


async def _obter_ou_criar_grupo(nome: str, db: AsyncSession) -> Grupo:
    grupo = await db.scalar(select(Grupo).where(Grupo.nome == nome))
    if grupo:
        return grupo

    grupo = Grupo(nome=nome)
    db.add(grupo)
    await db.flush()
    return grupo


async def _obter_ou_criar_subgrupo(nome: str, grupo_id: int, db: AsyncSession) -> Subgrupo:
    subgrupo = await db.scalar(
        select(Subgrupo).where(Subgrupo.nome == nome, Subgrupo.grupo_id == grupo_id)
    )
    if subgrupo:
        return subgrupo

    subgrupo = Subgrupo(nome=nome, grupo_id=grupo_id, orcamento_mensal=Decimal("0"))
    db.add(subgrupo)
    await db.flush()
    return subgrupo


async def listar_ultimos(n: int, db: AsyncSession) -> list[tuple[Lancamento, str]]:
    resultado = await db.execute(
        select(Lancamento, Grupo.nome)
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .order_by(Lancamento.criado_em.desc())
        .limit(n)
    )
    return [(row[0], row[1]) for row in resultado.all()]


async def cancelar_lancamento(lancamento_id: int, db: AsyncSession) -> LancamentoInfo | None:
    resultado = await db.execute(
        select(Lancamento.id, Lancamento.descricao, Lancamento.valor, Lancamento.data_gasto, Grupo.nome)
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .where(Lancamento.id == lancamento_id)
    )
    row = resultado.first()
    if row is None:
        return None

    lc_id, descricao, valor, data_gasto, grupo_nome = row
    lancamento = await db.get(Lancamento, lc_id)
    await db.delete(lancamento)
    await db.commit()

    return LancamentoInfo(
        id=lc_id,
        descricao=descricao,
        valor=Decimal(str(valor)),
        data_gasto=data_gasto,
        grupo_nome=grupo_nome,
    )


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()
