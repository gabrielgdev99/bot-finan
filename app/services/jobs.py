import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

import pytz
from sqlalchemy import extract, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.lancamento import Lancamento
from app.models.subgrupo import Subgrupo
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
                .options(selectinload(Lancamento.grupo), selectinload(Lancamento.subgrupo))
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
                categoria = f"{l.grupo.nome}/{l.subgrupo.nome}"

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
        from app.services.resumo import calcular_projecao, formatar_projecao

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
                .options(selectinload(Lancamento.grupo), selectinload(Lancamento.subgrupo))
                .order_by(Lancamento.grupo_id, Lancamento.subgrupo_id)
            )
            lancamentos = resultado.scalars().all()

            # Calcula projeção
            projecao = await calcular_projecao(mes_atual, ano_atual, session)

        # Agrupa: grupo_nome -> subgrupo -> total
        grupos: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for l in lancamentos:
            grupo_nome = l.grupo.nome
            subgrupo = l.subgrupo.nome
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

        # Anexa projeção se disponível
        if projecao is not None:
            linhas.append("")
            linhas.append(formatar_projecao(projecao, mes_atual, ano_atual))

        texto = "\n".join(linhas)

        await enviar_mensagem(settings.WHATSAPP_GROUP_ID, texto)
        logger.info("job_resumo_bidiario concluido | mes=%d/%d | lancamentos=%d", mes_atual, ano_atual, len(lancamentos))

    except Exception:
        logger.exception("job_resumo_bidiario falhou")


async def job_comparativo_mensal() -> None:
    """Envia comparativo do mês que fechou vs mês anterior. Roda todo dia 1 às 08h00 BRT."""
    try:
        from app.services.resumo import calcular_comparativo, formatar_comparativo

        agora = datetime.now(BRT)
        # No dia 1, comparamos o mês anterior (M-1) vs o mês anterior ao anterior (M-2)
        # Exemplo: 1º de junho, compara maio vs abril
        mes_a_comparar = agora.month - 1 if agora.month > 1 else 12
        ano_a_comparar = agora.year if agora.month > 1 else agora.year - 1

        async with AsyncSessionLocal() as session:
            comparativo = await calcular_comparativo(mes_a_comparar, ano_a_comparar, session)

        # Se não há grupos para comparar, não envia nada
        if not comparativo.grupos:
            logger.info("job_comparativo_mensal | nenhum gasto registrado em nenhum dos meses")
            return

        texto = formatar_comparativo(comparativo)
        await enviar_mensagem(settings.WHATSAPP_GROUP_ID, texto)
        logger.info("job_comparativo_mensal concluido | mes=%d/%d | grupos=%d", mes_a_comparar, ano_a_comparar, len(comparativo.grupos))

    except Exception:
        logger.exception("job_comparativo_mensal falhou")


async def job_processar_lembretes() -> None:
    """Processa lembretes: avisa 2 dias antes (manual) ou lança no próprio dia (auto)."""
    try:
        from app.services.lancamento import salvar_lancamento_de_template
        from app.services.lembrete import processar_lembretes_do_dia

        async with AsyncSessionLocal() as session:
            lembretes_aviso, lembretes_auto = await processar_lembretes_do_dia(session)

        # Envia avisos para lembretes manuais (2 dias antes)
        for lembrete in lembretes_aviso:
            template = lembrete.template
            valor_fmt = _fmt(template.valor)
            categoria = f"{template.subgrupo.grupo.nome} > {template.subgrupo.nome}"
            texto = f"⏰ {template.nome} vence em 2 dias (dia {lembrete.dia_vencimento})!\n{template.descricao} — R$ {valor_fmt} → {categoria}\n\nResponda *lançar {template.nome}* para registrar automaticamente."
            await enviar_mensagem(settings.WHATSAPP_GROUP_ID, texto)
            logger.info("job_processar_lembretes | aviso enviado | template=%s", template.nome)

        # Lança automaticamente para lembretes auto (no próprio dia)
        async with AsyncSessionLocal() as session:
            for lembrete in lembretes_auto:
                template = lembrete.template
                lancamento = await salvar_lancamento_de_template(template.nome, session)
                if lancamento:
                    valor_fmt = _fmt(template.valor)
                    categoria = f"{template.subgrupo.grupo.nome} > {template.subgrupo.nome}"
                    texto = f"✅ Lançamento automático: {template.nome}\n{template.descricao} — R$ {valor_fmt} → {categoria}"
                    await enviar_mensagem(settings.WHATSAPP_GROUP_ID, texto)
                    logger.info("job_processar_lembretes | lançamento automático | template=%s", template.nome)

        if lembretes_aviso or lembretes_auto:
            logger.info("job_processar_lembretes concluido | avisos=%d | auto=%d", len(lembretes_aviso), len(lembretes_auto))

    except Exception:
        logger.exception("job_processar_lembretes falhou")
