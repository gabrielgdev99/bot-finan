import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

import pytz
from sqlalchemy import extract, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.lancamento import Lancamento
from app.services.whatsapp import enviar_mensagem

logger = logging.getLogger(__name__)

BRT = pytz.timezone("America/Sao_Paulo")


def _fmt(valor) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def job_resumo_diario() -> None:
    """Envia resumo dos gastos de ontem. Roda diariamente às 06h00 BRT."""
    try:
        ontem: date = (datetime.now(BRT) - timedelta(days=1)).date()

        async with AsyncSessionLocal() as session:
            resultado = await session.execute(
                select(Lancamento)
                .where(Lancamento.data_gasto == ontem)
                .options(selectinload(Lancamento.grupo))
                .order_by(Lancamento.descricao)
            )
            lancamentos = resultado.scalars().all()

        if not lancamentos:
            texto = "📭 Nenhum gasto registrado ontem."
        else:
            data_str = ontem.strftime("%d/%m/%y")
            linhas = [f"📅 *Gastos de ontem ({data_str}):*\n"]

            total = sum(l.valor for l in lancamentos)

            for l in lancamentos:
                categoria = l.grupo.nome
                if l.subgrupo:
                    categoria = f"{categoria}/{l.subgrupo}"

                linha = f"• {l.descricao} — R$ {_fmt(l.valor)} | {categoria}"
                if l.cartao:
                    linha += f" | 💳 {l.cartao}"
                linhas.append(linha)

            linhas.append(f"\n*Total: R$ {_fmt(total)}*")
            texto = "\n".join(linhas)

        await enviar_mensagem(settings.WHATSAPP_GROUP_ID, texto)
        logger.info("job_resumo_diario concluido | data=%s | lancamentos=%d", ontem, len(lancamentos) if lancamentos else 0)

    except Exception:
        logger.exception("job_resumo_diario falhou")


async def job_resumo_bidiario() -> None:
    """Envia resumo mensal agrupado por grupo e subgrupo. Roda a cada 2 dias às 08h00 BRT."""
    try:
        agora = datetime.now(BRT)
        mes_atual = agora.month
        ano_atual = agora.year

        async with AsyncSessionLocal() as session:
            resultado = await session.execute(
                select(Lancamento)
                .where(
                    extract("month", Lancamento.data_pagamento) == mes_atual,
                    extract("year", Lancamento.data_pagamento) == ano_atual,
                )
                .options(selectinload(Lancamento.grupo))
                .order_by(Lancamento.grupo_id, Lancamento.subgrupo)
            )
            lancamentos = resultado.scalars().all()

        # Agrupa: grupo_nome -> subgrupo -> total
        grupos: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for l in lancamentos:
            grupo_nome = l.grupo.nome
            subgrupo = l.subgrupo or "Outros"
            grupos[grupo_nome][subgrupo] += float(l.valor)

        mes_nome = agora.strftime("%b/%y").capitalize()
        linhas = [f"📊 *Resumo do mês ({mes_nome}):*\n"]

        total_geral = 0.0
        for grupo_nome in sorted(grupos):
            subgrupos = grupos[grupo_nome]
            total_grupo = sum(subgrupos.values())
            total_geral += total_grupo

            linhas.append(f"*{grupo_nome}* — R$ {_fmt(total_grupo)}")
            for sub_nome in sorted(subgrupos):
                linhas.append(f"  • {sub_nome}: R$ {_fmt(subgrupos[sub_nome])}")
            linhas.append("")

        linhas.append(f"*Total geral: R$ {_fmt(total_geral)}*")
        texto = "\n".join(linhas)

        await enviar_mensagem(settings.WHATSAPP_GROUP_ID, texto)
        logger.info("job_resumo_bidiario concluido | mes=%d/%d | lancamentos=%d", mes_atual, ano_atual, len(lancamentos))

    except Exception:
        logger.exception("job_resumo_bidiario falhou")
