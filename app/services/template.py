import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grupo import Grupo
from app.models.subgrupo import Subgrupo
from app.models.template import Template

logger = logging.getLogger(__name__)


async def criar_template(
    nome: str,
    descricao: str,
    valor: Decimal,
    grupo_nome: str,
    subgrupo_nome: str,
    cartao: str | None,
    db: AsyncSession,
) -> Template | None:
    """
    Cria um novo template.
    Retorna None se grupo ou subgrupo não existem.
    """
    grupo = await db.scalar(select(Grupo).where(Grupo.nome == grupo_nome))
    if not grupo:
        logger.warning("Grupo não encontrado ao criar template | grupo=%s", grupo_nome)
        return None

    subgrupo = await db.scalar(
        select(Subgrupo).where(Subgrupo.nome == subgrupo_nome, Subgrupo.grupo_id == grupo.id)
    )
    if not subgrupo:
        logger.warning("Subgrupo não encontrado ao criar template | grupo=%s | subgrupo=%s", grupo_nome, subgrupo_nome)
        return None

    template = Template(
        nome=nome,
        descricao=descricao,
        valor=valor,
        subgrupo_id=subgrupo.id,
        cartao=cartao,
    )
    db.add(template)

    try:
        await db.commit()
        await db.refresh(template)
        logger.info("Template criado | nome=%s | grupo=%s | subgrupo=%s | valor=%s", nome, grupo_nome, subgrupo_nome, valor)
        return template
    except IntegrityError:
        await db.rollback()
        logger.warning("Template duplicado ou conflito | nome=%s", nome)
        return None


async def remover_template(nome: str, db: AsyncSession) -> Template | None:
    """Remove um template por nome. Retorna o template removido ou None se não encontrado."""
    template = await db.scalar(select(Template).where(Template.nome == nome))
    if not template:
        logger.warning("Template não encontrado ao remover | nome=%s", nome)
        return None

    await db.delete(template)
    await db.commit()
    logger.info("Template removido | nome=%s", nome)
    return template


async def resolver_template(nome: str, db: AsyncSession) -> Template | None:
    """Busca um template por nome (case-sensitive por enquanto)."""
    return await db.scalar(select(Template).where(Template.nome == nome))


async def listar_templates(db: AsyncSession) -> list[Template]:
    """Lista todos os templates cadastrados."""
    resultado = await db.execute(select(Template).order_by(Template.nome))
    return resultado.scalars().all()
