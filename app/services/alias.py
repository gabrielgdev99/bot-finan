import logging
import unicodedata
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alias import Alias
from app.models.grupo import Grupo
from app.models.subgrupo import Subgrupo

logger = logging.getLogger(__name__)


def _normalizar_palavra_chave(texto: str) -> str:
    """Normaliza palavra-chave: lowercase, sem acentuação."""
    texto = texto.lower().strip()
    texto_nfd = unicodedata.normalize('NFD', texto)
    return ''.join(c for c in texto_nfd if unicodedata.category(c) != 'Mn')


async def criar_alias(
    palavra_chave: str,
    grupo_nome: str,
    subgrupo_nome: str,
    db: AsyncSession,
) -> Alias | None:
    """
    Cria um novo alias.
    Retorna None se grupo ou subgrupo não existem.
    """
    grupo = await db.scalar(select(Grupo).where(Grupo.nome == grupo_nome))
    if not grupo:
        logger.warning("Grupo não encontrado ao criar alias | grupo=%s", grupo_nome)
        return None

    subgrupo = await db.scalar(
        select(Subgrupo).where(
            Subgrupo.nome == subgrupo_nome,
            Subgrupo.grupo_id == grupo.id
        )
    )
    if not subgrupo:
        logger.warning("Subgrupo não encontrado ao criar alias | grupo=%s | subgrupo=%s", grupo_nome, subgrupo_nome)
        return None

    palavra_normalizada = _normalizar_palavra_chave(palavra_chave)
    alias = Alias(
        palavra_chave=palavra_normalizada,
        subgrupo_id=subgrupo.id,
    )
    db.add(alias)

    try:
        await db.commit()
        await db.refresh(alias)
        logger.info("Alias criado | palavra_chave=%s | grupo=%s | subgrupo=%s", palavra_normalizada, grupo_nome, subgrupo_nome)
        return alias
    except IntegrityError:
        await db.rollback()
        logger.warning("Alias duplicado ou conflito | palavra_chave=%s", palavra_normalizada)
        return None


async def remover_alias(palavra_chave: str, db: AsyncSession) -> Alias | None:
    """Remove um alias por palavra-chave. Retorna o alias removido ou None se não encontrado."""
    palavra_normalizada = _normalizar_palavra_chave(palavra_chave)
    alias = await db.scalar(select(Alias).where(Alias.palavra_chave == palavra_normalizada))
    if not alias:
        logger.warning("Alias não encontrado ao remover | palavra_chave=%s", palavra_normalizada)
        return None

    await db.delete(alias)
    await db.commit()
    logger.info("Alias removido | palavra_chave=%s", palavra_normalizada)
    return alias


async def resolver_alias(palavra_chave: str, db: AsyncSession) -> Alias | None:
    """Busca um alias por palavra-chave (case-insensitive, sem acentuação)."""
    palavra_normalizada = _normalizar_palavra_chave(palavra_chave)
    return await db.scalar(select(Alias).where(Alias.palavra_chave == palavra_normalizada))


async def listar_aliases(db: AsyncSession) -> list[Alias]:
    """Lista todos os aliases cadastrados."""
    resultado = await db.execute(select(Alias).order_by(Alias.palavra_chave))
    return resultado.scalars().all()
