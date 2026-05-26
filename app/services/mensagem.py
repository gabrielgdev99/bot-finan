import logging
from datetime import date

from app.core.database import AsyncSessionLocal
from app.services.parser import (
    parse_alias,
    parse_cancela,
    parse_historico,
    parse_lancamento,
    parse_lancamento_multiplo,
    parse_orcamento,
    parse_relatorio_cartao,
    parse_remove_alias,
    parse_remove_template,
    parse_resumo_comando,
    parse_resumo_periodo,
    parse_template,
    parse_ultimos,
)

logger = logging.getLogger(__name__)


async def processar_mensagem(texto: str, tipo: str, grupo_id: str) -> None:
    from app.services.lancamento import cancelar_lancamento, definir_orcamento, listar_ultimos, salvar_lancamento, salvar_lancamento_de_template
    from app.services.resumo import (
        calcular_historico,
        calcular_projecao,
        calcular_relatorio_cartao,
        calcular_resumo,
        calcular_resumo_periodo,
        calcular_resumo_subgrupos,
        calcular_resumo_todos,
        formatar_ajuda,
        formatar_cancela_nao_encontrado,
        formatar_cancela_sucesso,
        formatar_cartao_nao_encontrado,
        formatar_confirmacao_orcamento,
        formatar_historico,
        formatar_projecao,
        formatar_relatorio_cartao,
        formatar_resumo_lancamento,
        formatar_resumo_parcelas,
        formatar_resumo_periodo,
        formatar_resumo_subgrupos,
        formatar_resumo_todos,
        formatar_ultimos,
    )
    from app.services.template import criar_template, listar_templates, remover_template, resolver_template
    from app.services.whatsapp import enviar_mensagem

    async with AsyncSessionLocal() as db:
        if tipo == "alias":
            from app.services.alias import criar_alias

            dto = parse_alias(texto)
            if dto is None:
                return

            alias = await criar_alias(
                palavra_chave=dto.palavra_chave,
                grupo_nome=dto.grupo,
                subgrupo_nome=dto.subgrupo,
                db=db,
            )
            if alias is None:
                resposta = f"❌ Grupo ou subgrupo não encontrado: '{dto.grupo}' > '{dto.subgrupo}'\nTente criar primeiro com um lançamento normal."
            else:
                resposta = f'✅ Alias criado: "{dto.palavra_chave}" → {dto.grupo} > {dto.subgrupo}'
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "remove_alias":
            from app.services.alias import remover_alias

            dto = parse_remove_alias(texto)
            if dto is None:
                return

            removido = await remover_alias(dto.palavra_chave, db)
            if removido is None:
                resposta = f"❌ Alias '{dto.palavra_chave}' não encontrado."
            else:
                resposta = f'✅ Alias "{removido.palavra_chave}" removido.'
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "list_aliases":
            from app.services.alias import listar_aliases

            aliases = await listar_aliases(db)
            resposta = _formatar_listar_aliases(aliases)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "erro_parcelas":
            from app.services.parser import detectar_erro_parcelas
            erro = detectar_erro_parcelas(texto)
            await enviar_mensagem(grupo_id, erro)

        elif tipo == "lancamento":
            dto = parse_lancamento(texto)
            if dto is None:
                return

            resultado = await salvar_lancamento(dto, db)
            if resultado is None:
                return  # duplicata — silencioso

            hoje = date.today()
            resumo = await calcular_resumo(dto.grupo, hoje.month, hoje.year, db)

            if isinstance(resultado, list):
                resposta = formatar_resumo_parcelas(resumo, resultado, dto)
            else:
                resposta = formatar_resumo_lancamento(resumo, resultado.id)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "lancamento_multiplo":
            try:
                parse_result = parse_lancamento_multiplo(texto)
                if parse_result is None:
                    return

                data_cabecalho, linhas_lancamento = parse_result
                lancamentos_salvos = []
                erros = []

                for idx, linha in enumerate(linhas_lancamento, 1):
                    dto = parse_lancamento(f"{data_cabecalho.strftime('%d/%m/%y')} - {linha}")
                    if dto is None:
                        erros.append((idx, linha, "Formato inválido ou incompleto"))
                        continue

                    resultado = await salvar_lancamento(dto, db)
                    if resultado is None:
                        erros.append((idx, linha, "Duplicada (já foi processada)"))
                        continue

                    lancamentos_salvos.append((dto, resultado))

                if not lancamentos_salvos and erros:
                    linhas_msg = [f"❌ Nenhum lançamento foi salvo."]
                    for idx, _, msg_erro in erros:
                        linhas_msg.append(f"  Linha {idx}: {msg_erro}")
                    resposta = "\n".join(linhas_msg)
                    await enviar_mensagem(grupo_id, resposta)
                    return

                hoje = date.today()
                resposta = await _formatar_resposta_multiplo(lancamentos_salvos, erros, data_cabecalho.month, data_cabecalho.year, db)
                await enviar_mensagem(grupo_id, resposta)
            except Exception as e:
                logger.exception("Erro ao processar lancamento multiplo: %s", e)
                return

        elif tipo == "orcamento":
            dto = parse_orcamento(texto)
            if dto is None:
                return

            subgrupo = await definir_orcamento(dto, db)
            resposta = formatar_confirmacao_orcamento(dto.grupo, subgrupo.nome, subgrupo.orcamento_mensal, dto.mes)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "cartao":
            dto = parse_relatorio_cartao(texto)
            if dto is None:
                return

            hoje = date.today()
            mes = dto.mes or hoje.month
            ano = dto.ano or hoje.year
            resultado = await calcular_relatorio_cartao(dto.cartao, mes, ano, db)
            if resultado is None:
                resposta = formatar_cartao_nao_encontrado(dto.cartao)
            else:
                resposta = formatar_relatorio_cartao(resultado)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "resumo_periodo":
            dto = parse_resumo_periodo(texto)
            if dto is None:
                return

            if dto.data_inicio > dto.data_fim:
                resposta = "❌ Período inválido: data inicial não pode ser posterior à final."
                await enviar_mensagem(grupo_id, resposta)
                return

            grupos = await calcular_resumo_periodo(dto.data_inicio, dto.data_fim, db)
            if grupos is None:
                resposta = "📭 Nenhum lançamento no período informado."
            else:
                resposta = formatar_resumo_periodo(grupos, dto.data_inicio, dto.data_fim)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "resumo_comando":
            dto = parse_resumo_comando(texto)
            if dto is None:
                return

            hoje = date.today()
            mes = dto.mes or hoje.month
            ano = dto.ano or hoje.year

            if dto.grupo:
                resultado = await calcular_resumo_subgrupos(dto.grupo, mes, ano, db)
                if resultado is None:
                    mes_str = f"{mes:02d}/{str(ano)[2:]}"
                    resposta = f"📭 Nenhum gasto encontrado para *{dto.grupo}* em {mes_str}."
                else:
                    resposta = formatar_resumo_subgrupos(resultado, mes, ano)
            else:
                resumos = await calcular_resumo_todos(mes, ano, db)
                resposta = formatar_resumo_todos(resumos, mes, ano)

                # Anexa projeção ao resumo geral
                projecao = await calcular_projecao(mes, ano, db)
                if projecao is not None:
                    resposta += "\n\n" + formatar_projecao(projecao, mes, ano)

            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "ultimos":
            dto = parse_ultimos(texto)
            if dto is None:
                return

            if dto.n > 20:
                await enviar_mensagem(grupo_id, "❌ Máximo de 20 lançamentos por consulta.\nUse: `ultimos: N` com N ≤ 20")
                return

            lancamentos = await listar_ultimos(dto.n, db)
            resposta = formatar_ultimos(lancamentos)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "cancela":
            dto = parse_cancela(texto)
            if dto is None:
                return

            info = await cancelar_lancamento(dto.lancamento_id, db)
            if info is None:
                resposta = formatar_cancela_nao_encontrado(dto.lancamento_id)
            else:
                hoje = date.today()
                novo_resumo = await calcular_resumo(info.grupo_nome, hoje.month, hoje.year, db)
                resposta = formatar_cancela_sucesso(info, novo_resumo)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "historico":
            from app.models.grupo import Grupo
            from app.models.subgrupo import Subgrupo
            from sqlalchemy import select

            dto = parse_historico(texto)
            if dto is None:
                return

            # Busca o grupo
            grupo = await db.scalar(select(Grupo).where(Grupo.nome == dto.grupo))
            if grupo is None:
                resposta = f"❌ Grupo *{dto.grupo}* não encontrado."
                await enviar_mensagem(grupo_id, resposta)
                return

            # Se informou subgrupo, busca e valida
            subgrupo_id = None
            subgrupo_nome = None
            if dto.subgrupo:
                subgrupo = await db.scalar(
                    select(Subgrupo).where(
                        Subgrupo.grupo_id == grupo.id,
                        Subgrupo.nome == dto.subgrupo,
                    )
                )
                if subgrupo is None:
                    resposta = f"❌ Subgrupo *{dto.grupo} > {dto.subgrupo}* não encontrado."
                    await enviar_mensagem(grupo_id, resposta)
                    return
                subgrupo_id = subgrupo.id
                subgrupo_nome = subgrupo.nome

            # Calcula histórico
            historico = await calcular_historico(grupo.id, subgrupo_id, db)
            if historico is None:
                resposta = f"❌ Erro ao carregar histórico."
                await enviar_mensagem(grupo_id, resposta)
                return

            resposta = formatar_historico(historico, grupo.nome, subgrupo_nome)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "template":
            dto = parse_template(texto)
            if dto is None:
                return

            template = await criar_template(
                nome=dto.nome,
                descricao=dto.descricao,
                valor=dto.valor,
                grupo_nome=dto.grupo,
                subgrupo_nome=dto.subgrupo,
                cartao=dto.cartao,
                db=db,
            )
            if template is None:
                resposta = f"❌ Grupo ou subgrupo não encontrado: '{dto.grupo}' > '{dto.subgrupo}'\nTente criar primeiro com um lançamento normal."
            else:
                resposta = _formatar_template_criado(template, dto.grupo, dto.subgrupo)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "remove_template":
            dto = parse_remove_template(texto)
            if dto is None:
                return

            removido = await remover_template(dto.nome, db)
            if removido is None:
                resposta = f"❌ Template '{dto.nome}' não encontrado."
            else:
                resposta = f'✅ Template "{removido.nome}" removido.'
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "templates":
            templates = await listar_templates(db)
            resposta = _formatar_listar_templates(templates)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "possivel_template":
            template = await resolver_template(texto.strip(), db)
            if template is not None:
                lancamento = await salvar_lancamento_de_template(template.nome, db)
                if lancamento is None:
                    return

                hoje = date.today()
                resumo = await calcular_resumo(template.subgrupo.grupo.nome, hoje.month, hoje.year, db)
                resposta = formatar_resumo_lancamento(resumo, lancamento.id)
                await enviar_mensagem(grupo_id, resposta)
            else:
                await enviar_mensagem(grupo_id, formatar_ajuda())

        else:  # "ajuda" ou "desconhecido"
            await enviar_mensagem(grupo_id, formatar_ajuda())


def _fmt(valor):
    """Formata valor monetário."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_template_criado(template, grupo_nome: str, subgrupo_nome: str) -> str:
    """Formata resposta de template criado com sucesso."""
    valor_fmt = _fmt(template.valor)
    return f'✅ Template "{template.nome}" criado: {template.descricao} — R$ {valor_fmt} → {grupo_nome} > {subgrupo_nome}'


def _formatar_listar_templates(templates: list) -> str:
    """Formata lista de templates."""
    if not templates:
        return "📋 Nenhum template cadastrado."

    linhas = ["📋 Templates cadastrados:"]
    for t in templates:
        valor_fmt = _fmt(t.valor)
        cartao_str = f" | {t.cartao}" if t.cartao else ""
        grupo_nome = t.subgrupo.grupo.nome
        linhas.append(f"• {t.nome} → {t.descricao} | R$ {valor_fmt} | {grupo_nome} > {t.subgrupo.nome}{cartao_str}")

    return "\n".join(linhas)


def _formatar_listar_aliases(aliases: list) -> str:
    """Formata lista de aliases."""
    if not aliases:
        return "📋 Nenhum alias cadastrado."

    linhas = ["📋 Aliases cadastrados:"]
    for a in aliases:
        grupo_nome = a.subgrupo.grupo.nome
        linhas.append(f"• {a.palavra_chave} → {grupo_nome} > {a.subgrupo.nome}")

    return "\n".join(linhas)


async def _formatar_resposta_multiplo(lancamentos_salvos, erros, mes, ano, db) -> str:
    from decimal import Decimal
    from sqlalchemy import select, extract, func
    from app.models.lancamento import Lancamento
    from app.models.grupo import Grupo

    linhas = [f"✅ {len(lancamentos_salvos)} lançamento{'s' if len(lancamentos_salvos) != 1 else ''} salvo{'s' if len(lancamentos_salvos) != 1 else ''}!"]

    # Lista lançamentos salvos
    for dto, resultado in lancamentos_salvos:
        valor_fmt = _fmt(dto.valor)
        grupo_subgrupo = f"{dto.grupo} > {dto.subgrupo}"
        if isinstance(resultado, list):
            linhas.append(f"• {dto.descricao} — R$ {valor_fmt} em {dto.parcelas}x → {grupo_subgrupo}")
        else:
            linhas.append(f"• {dto.descricao} — R$ {valor_fmt} → {grupo_subgrupo}")

    # Erros, se houver
    if erros:
        linhas.append("")
        for idx, linha, msg_erro in erros:
            linhas.append(f"⚠️ Linha {idx}: {msg_erro}")

    # Resumo por grupo afetado
    linhas.append("")
    grupos_afetados = {}
    for dto, _ in lancamentos_salvos:
        if dto.grupo not in grupos_afetados:
            grupos_afetados[dto.grupo] = {
                "total": Decimal("0"),
                "orcamento": Decimal("0"),
            }

    resultado = await db.execute(
        select(
            Grupo.nome,
            func.coalesce(func.sum(Lancamento.valor), Decimal("0")),
        )
        .join(Lancamento, Grupo.id == Lancamento.grupo_id)
        .where(
            Grupo.nome.in_(list(grupos_afetados.keys())),
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Grupo.id, Grupo.nome)
    )
    for row in resultado:
        grupo_nome, total = row
        grupos_afetados[grupo_nome]["total"] = Decimal(str(total))

    # Busca orçamentos
    from app.models.subgrupo import Subgrupo
    resultado_orcamento = await db.execute(
        select(
            Grupo.nome,
            func.coalesce(func.sum(Subgrupo.orcamento_mensal), Decimal("0")),
        )
        .join(Subgrupo, Grupo.id == Subgrupo.grupo_id)
        .where(Grupo.nome.in_(list(grupos_afetados.keys())))
        .group_by(Grupo.id, Grupo.nome)
    )
    for row in resultado_orcamento:
        grupo_nome, orcamento = row
        grupos_afetados[grupo_nome]["orcamento"] = Decimal(str(orcamento))

    # Formata resumo por grupo
    for grupo_nome in sorted(grupos_afetados.keys()):
        info = grupos_afetados[grupo_nome]
        total_fmt = _fmt(info["total"])
        if info["orcamento"] > 0:
            orcamento_fmt = _fmt(info["orcamento"])
            restante = info["orcamento"] - info["total"]
            restante_fmt = _fmt(restante)
            pct = (info["total"] / info["orcamento"] * 100).quantize(Decimal("1"))
            linhas.append(f"📊 {grupo_nome}: R$ {total_fmt} | Orçamento: R$ {orcamento_fmt} | Restante: R$ {restante_fmt} ({pct}%)")
        else:
            linhas.append(f"📊 {grupo_nome}: R$ {total_fmt} gastos")

    return "\n".join(linhas)
