import logging
from datetime import date

from app.core.database import AsyncSessionLocal
from app.services.parser import (
    parse_cancela,
    parse_lancamento,
    parse_orcamento,
    parse_relatorio_cartao,
    parse_resumo_comando,
    parse_ultimos,
)

logger = logging.getLogger(__name__)


async def processar_mensagem(texto: str, tipo: str, grupo_id: str) -> None:
    from app.services.lancamento import cancelar_lancamento, definir_orcamento, listar_ultimos, salvar_lancamento
    from app.services.resumo import (
        calcular_relatorio_cartao,
        calcular_resumo,
        calcular_resumo_subgrupos,
        calcular_resumo_todos,
        formatar_ajuda,
        formatar_cancela_nao_encontrado,
        formatar_cancela_sucesso,
        formatar_cartao_nao_encontrado,
        formatar_confirmacao_orcamento,
        formatar_relatorio_cartao,
        formatar_resumo_lancamento,
        formatar_resumo_subgrupos,
        formatar_resumo_todos,
        formatar_ultimos,
    )
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

        else:  # "ajuda" ou "desconhecido"
            await enviar_mensagem(grupo_id, formatar_ajuda())
