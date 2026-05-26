import hashlib
import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alias import Alias
from app.models.grupo import Grupo
from app.models.lancamento import Lancamento
from app.models.orcamento_mensal import OrcamentoMensal
from app.models.subgrupo import Subgrupo
from app.schemas import LancamentoDTO, LancamentoInfo, OrcamentoDTO
from app.services import alias as alias_service

logger = logging.getLogger(__name__)


async def salvar_lancamento(
    dto: LancamentoDTO,
    db: AsyncSession,
) -> Lancamento | list[Lancamento] | None:
    hash_msg = _hash(dto.texto_original)

    duplicata = await db.scalar(select(Lancamento).where(Lancamento.hash_msg == hash_msg))
    if duplicata:
        logger.info("Lançamento duplicado ignorado | hash=%s", hash_msg)
        return None

    grupo_nome = dto.grupo
    subgrupo_nome = dto.subgrupo

    if not grupo_nome or not subgrupo_nome:
        alias = await alias_service.resolver_alias(dto.descricao, db)
        if alias:
            grupo_nome = alias.subgrupo.grupo.nome
            subgrupo_nome = alias.subgrupo.nome
            logger.info("Alias resolvido | palavra_chave=%s | grupo=%s | subgrupo=%s", dto.descricao, grupo_nome, subgrupo_nome)
        else:
            logger.warning("Grupo/subgrupo ausentes e alias não encontrado | descricao=%s", dto.descricao)
            return None

    grupo = await _obter_ou_criar_grupo(grupo_nome, db)
    subgrupo = await _obter_ou_criar_subgrupo(subgrupo_nome, grupo.id, db)

    if dto.parcelas > 1:
        lancamentos = await _salvar_parcelas(
            dto, grupo.id, subgrupo.id, hash_msg, db
        )
        logger.info("Lançamento parcelado salvo | parcelas=%d | grupo=%s | valor_total=%s", dto.parcelas, dto.grupo, dto.valor)
        return lancamentos

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


async def salvar_lancamento_de_template(
    template_nome: str,
    db: AsyncSession,
) -> Lancamento | None:
    """Salva um lançamento usando dados de um template com data de hoje."""
    from datetime import date
    from app.models.template import Template

    template = await db.scalar(select(Template).where(Template.nome == template_nome))
    if not template:
        logger.warning("Template não encontrado para lançamento | nome=%s", template_nome)
        return None

    hoje = date.today()
    # Hash único para cada uso do template (inclui a data de hoje no hash para evitar duplicação no mesmo dia)
    hash_msg = _hash(f"{template_nome}_{hoje.isoformat()}")

    duplicata = await db.scalar(select(Lancamento).where(Lancamento.hash_msg == hash_msg))
    if duplicata:
        logger.info("Lançamento de template duplicado ignorado | template=%s | data=%s", template_nome, hoje)
        return None

    lancamento = Lancamento(
        data_gasto=hoje,
        descricao=template.descricao,
        valor=template.valor,
        grupo_id=template.subgrupo.grupo_id,
        subgrupo_id=template.subgrupo_id,
        cartao=template.cartao,
        data_pagamento=hoje,
        hash_msg=hash_msg,
    )
    db.add(lancamento)

    try:
        await db.commit()
        await db.refresh(lancamento)
        logger.info("Lançamento de template salvo | id=%s | template=%s | valor=%s", lancamento.id, template_nome, template.valor)
        return lancamento
    except IntegrityError:
        await db.rollback()
        logger.warning("Conflito de hash ao salvar lançamento de template | template=%s", template_nome)
        return None


async def definir_orcamento(dto: OrcamentoDTO, db: AsyncSession) -> Subgrupo:
    grupo = await _obter_ou_criar_grupo(dto.grupo, db)
    subgrupo = await _obter_ou_criar_subgrupo(dto.subgrupo, grupo.id, db)

    if dto.mes:
        orcamento_mensal = await db.scalar(
            select(OrcamentoMensal).where(
                OrcamentoMensal.grupo_id == grupo.id,
                OrcamentoMensal.mes == dto.mes,
            )
        )
        if orcamento_mensal:
            orcamento_mensal.valor = dto.valor
        else:
            orcamento_mensal = OrcamentoMensal(grupo_id=grupo.id, mes=dto.mes, valor=dto.valor)
            db.add(orcamento_mensal)
        logger.info("Orçamento mensal definido | grupo=%s | mes=%s | valor=%s", dto.grupo, dto.mes, dto.valor)
    else:
        subgrupo.orcamento_mensal = dto.valor
        logger.info("Orçamento genérico definido | grupo=%s | subgrupo=%s | valor=%s", dto.grupo, dto.subgrupo, dto.valor)

    await db.commit()
    await db.refresh(subgrupo)
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


async def _salvar_parcelas(
    dto: LancamentoDTO,
    grupo_id: int,
    subgrupo_id: int,
    hash_base: str,
    db: AsyncSession,
) -> list[Lancamento] | None:
    valor_parcela = (dto.valor / dto.parcelas).quantize(Decimal("0.01"))
    lancamentos_salvos = []

    data_pagamento = dto.inicio_parcela
    for i in range(1, dto.parcelas + 1):
        hash_msg = _hash(f"{hash_base}_{i}")

        duplicata = await db.scalar(select(Lancamento).where(Lancamento.hash_msg == hash_msg))
        if duplicata:
            await db.rollback()
            logger.warning("Parcela duplicada durante salvar | hash=%s", hash_msg)
            return None

        descricao_parcela = f"{dto.descricao} ({i}/{dto.parcelas})"

        lancamento = Lancamento(
            data_gasto=dto.data_gasto,
            descricao=descricao_parcela,
            valor=valor_parcela,
            grupo_id=grupo_id,
            subgrupo_id=subgrupo_id,
            cartao=dto.cartao,
            data_pagamento=data_pagamento,
            hash_msg=hash_msg,
        )
        db.add(lancamento)
        lancamentos_salvos.append(lancamento)

        if i < dto.parcelas:
            data_pagamento = _proximo_mes(data_pagamento)

    try:
        await db.commit()
        for lancamento in lancamentos_salvos:
            await db.refresh(lancamento)
        return lancamentos_salvos
    except IntegrityError:
        await db.rollback()
        logger.warning("Conflito de integridade ao salvar parcelas | hash_base=%s", hash_base)
        return None


def _proximo_mes(data):
    from datetime import date
    mes = data.month + 1
    ano = data.year
    if mes > 12:
        mes = 1
        ano += 1
    return date(ano, mes, 1)
