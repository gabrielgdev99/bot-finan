import logging
from datetime import date

from app.core.database import AsyncSessionLocal
from app.services.parser import (
    parse_cancela,
    parse_historico,
    parse_lancamento,
    parse_orcamento,
    parse_relatorio_cartao,
    parse_remove_template,
    parse_resumo_comando,
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
        formatar_resumo_subgrupos,
        formatar_resumo_todos,
        formatar_ultimos,
    )
    from app.services.template import criar_template, listar_templates, remover_template, resolver_template
    from app.services.whatsapp import enviar_mensagem

    async with AsyncSessionLocal() as db:
        if tipo == "lancamento":
            dto = parse_lancamento(texto)
            if dto is None:
                return

            lancamento = await salvar_lancamento(dto, db)
            if lancamento is None:
                return  # duplicata — silencioso

            hoje = date.today()
            resumo = await calcular_resumo(dto.grupo, hoje.month, hoje.year, db)
            resposta = formatar_resumo_lancamento(resumo, lancamento.id)
            await enviar_mensagem(grupo_id, resposta)

        elif tipo == "orcamento":
            dto = parse_orcamento(texto)
            if dto is None:
                return

            subgrupo = await definir_orcamento(dto, db)
            resposta = formatar_confirmacao_orcamento(dto.grupo, subgrupo.nome, subgrupo.orcamento_mensal)
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
