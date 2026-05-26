from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from calendar import monthrange

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grupo import Grupo
from app.models.lancamento import Lancamento
from app.models.orcamento_mensal import OrcamentoMensal
from app.models.subgrupo import Subgrupo
from app.schemas import HistoricoMesDTO, LancamentoInfo, ProjecaoDTO, ResumoPeriodoGrupoDTO

_MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


@dataclass
class ResumoDTO:
    grupo_nome: str
    total_gasto: Decimal
    orcamento_mensal: Decimal

    @property
    def restante(self) -> Decimal:
        return self.orcamento_mensal - self.total_gasto

    @property
    def tem_orcamento(self) -> bool:
        return self.orcamento_mensal > 0

    @property
    def percentual(self) -> Decimal | None:
        if not self.tem_orcamento:
            return None
        return (self.total_gasto / self.orcamento_mensal * 100).quantize(Decimal("1"))

    @property
    def alerta(self) -> str | None:
        pct = self.percentual
        if pct is None:
            return None
        if pct >= 100:
            return "estourado"
        if pct >= 80:
            return "aviso"
        return None


@dataclass
class ResumoSubgrupoDTO:
    grupo_nome: str
    total_gasto: Decimal
    orcamento_mensal: Decimal
    por_subgrupo: list[tuple[str, Decimal]]


@dataclass
class ResumoCartaoDTO:
    cartao: str
    mes: int
    ano: int
    total: Decimal
    por_grupo: list[tuple[str, Decimal]]


async def _obter_orcamento_grupo(grupo_id: int, mes: int, ano: int, db: AsyncSession) -> Decimal:
    data_mes = date(ano, mes, 1)
    orcamento_especifico = await db.scalar(
        select(OrcamentoMensal.valor).where(
            OrcamentoMensal.grupo_id == grupo_id,
            OrcamentoMensal.mes == data_mes,
        )
    )
    if orcamento_especifico:
        return Decimal(str(orcamento_especifico))
    resultado_generico = await db.execute(
        select(func.coalesce(func.sum(Subgrupo.orcamento_mensal), Decimal("0")))
        .where(Subgrupo.grupo_id == grupo_id)
    )
    return Decimal(str(resultado_generico.scalar()))


async def calcular_resumo(grupo_nome: str, mes: int, ano: int, db: AsyncSession) -> ResumoDTO:
    resultado = await db.execute(
        select(
            func.coalesce(func.sum(Lancamento.valor), Decimal("0")),
            Grupo.id
        )
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .where(
            Grupo.nome == grupo_nome,
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Grupo.id)
    )
    row = resultado.first()

    if row:
        total_gasto, grupo_id = row
        orcamento_mensal = await _obter_orcamento_grupo(grupo_id, mes, ano, db)
    else:
        total_gasto = Decimal("0")
        grupo = await db.scalar(select(Grupo).where(Grupo.nome == grupo_nome))
        if grupo:
            orcamento_mensal = await _obter_orcamento_grupo(grupo.id, mes, ano, db)
        else:
            orcamento_mensal = Decimal("0")

    return ResumoDTO(
        grupo_nome=grupo_nome,
        total_gasto=Decimal(str(total_gasto)),
        orcamento_mensal=Decimal(str(orcamento_mensal)),
    )


async def calcular_resumo_todos(mes: int, ano: int, db: AsyncSession) -> list[ResumoDTO]:
    resultado = await db.execute(
        select(
            Grupo.nome,
            Grupo.id,
            func.coalesce(func.sum(Lancamento.valor), Decimal("0"))
        )
        .join(Lancamento, Grupo.id == Lancamento.grupo_id)
        .where(
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Grupo.id, Grupo.nome)
        .order_by(Grupo.nome)
    )
    rows = resultado.all()

    resumos = []
    for row in rows:
        grupo_nome, grupo_id, total_gasto = row
        orcamento_mensal = await _obter_orcamento_grupo(grupo_id, mes, ano, db)
        resumos.append(
            ResumoDTO(
                grupo_nome=grupo_nome,
                total_gasto=Decimal(str(total_gasto)),
                orcamento_mensal=orcamento_mensal,
            )
        )
    return resumos


async def calcular_resumo_subgrupos(grupo_nome: str, mes: int, ano: int, db: AsyncSession) -> ResumoSubgrupoDTO | None:
    resultado = await db.execute(
        select(Subgrupo.nome, func.sum(Lancamento.valor))
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .join(Subgrupo, Lancamento.subgrupo_id == Subgrupo.id)
        .where(
            Grupo.nome == grupo_nome,
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Subgrupo.id, Subgrupo.nome)
        .order_by(Subgrupo.nome)
    )
    rows = resultado.all()
    if not rows:
        return None

    por_subgrupo = [(row[0], Decimal(str(row[1]))) for row in rows]
    total = sum(v for _, v in por_subgrupo)

    grupo = await db.scalar(select(Grupo).where(Grupo.nome == grupo_nome))
    if grupo:
        orcamento = await _obter_orcamento_grupo(grupo.id, mes, ano, db)
    else:
        orcamento = Decimal("0")

    return ResumoSubgrupoDTO(
        grupo_nome=grupo_nome,
        total_gasto=total,
        orcamento_mensal=orcamento,
        por_subgrupo=por_subgrupo,
    )


async def calcular_relatorio_cartao(cartao: str, mes: int, ano: int, db: AsyncSession) -> ResumoCartaoDTO | None:
    resultado = await db.execute(
        select(Grupo.nome, func.sum(Lancamento.valor))
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .where(
            func.lower(Lancamento.cartao) == cartao.lower(),
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Grupo.nome)
        .order_by(Grupo.nome)
    )
    rows = resultado.all()
    if not rows:
        return None

    por_grupo = [(row[0], Decimal(str(row[1]))) for row in rows]
    total = sum(v for _, v in por_grupo)
    return ResumoCartaoDTO(cartao=cartao, mes=mes, ano=ano, total=total, por_grupo=por_grupo)


def formatar_resumo_lancamento(resumo: ResumoDTO, lancamento_id: int) -> str:
    gasto_fmt = _fmt(resumo.total_gasto)
    linhas = [
        f"✅ Lançamento #{lancamento_id} salvo!",
        f"📂 {resumo.grupo_nome}: R$ {gasto_fmt} gastos este mês",
    ]
    if resumo.tem_orcamento:
        pct = resumo.percentual
        orcamento_fmt = _fmt(resumo.orcamento_mensal)
        restante_fmt = _fmt(resumo.restante)
        linhas.append(f"📊 Orçamento: R$ {orcamento_fmt} | Gasto: R$ {gasto_fmt} | Restante: R$ {restante_fmt} ({pct}%)")
        if resumo.alerta == "estourado":
            linhas.append("🚨 Orçamento estourado!")
        elif resumo.alerta == "aviso":
            linhas.append(f"⚠️ Atenção: {pct}% do orçamento utilizado")
    return "\n".join(linhas)


def formatar_confirmacao_orcamento(grupo_nome: str, subgrupo_nome: str, valor: Decimal, mes: date | None = None) -> str:
    valor_fmt = _fmt(valor)
    if mes:
        mes_fmt = mes.strftime("%m/%Y")
        return f'✅ Orçamento de "{grupo_nome}" para {mes_fmt} definido: R$ {valor_fmt}'
    else:
        return f'✅ Orçamento de "{grupo_nome}" definido: R$ {valor_fmt}/mês'


def formatar_ajuda() -> str:
    return (
        "❓ *Comandos disponíveis:*\n\n"
        "💰 *Lançamento:*\n"
        "`DD/MM/AA - descrição - valor - Grupo - Subgrupo`\n"
        "_(opcionais: `- cartao: nome` `- pagamento: DD/MM`)_\n"
        "Ex: `25/05/26 - padaria - 25 - Alimentação - Padaria`\n\n"
        "🏷️ *Aliases (lançamento curto):*\n"
        "`alias: padaria → Alimentação > Padaria`\n"
        "Usar: `25/05/26 - padaria - 25` (grupo/subgrupo inferidos pelo alias)\n"
        "Listar: `aliases` | Remover: `remove alias: padaria`\n\n"
        "💳 *Lançamento parcelado:*\n"
        "`DD/MM/AA - descrição - valor - Grupo - Subgrupo - parcelas: N - inicio: MM/AA`\n"
        "_(opcionais: `- cartao: nome`)_\n"
        "Ex: `01/05/26 - tv - 1200 - Casa - Eletrônicos - parcelas: 12 - inicio: 06/26`\n\n"
        "📋 *Orçamento:*\n"
        "`orçamento: grupo - subgrupo - valor`\n"
        "Ex: `orçamento: Alimentação - Mercado - 800`\n\n"
        "📅 *Orçamento para mês específico:*\n"
        "`orçamento: grupo - subgrupo - valor - mes: MM/AA`\n"
        "Ex: `orçamento: Alimentação - Mercado - 1000 - mes: 12/26`\n\n"
        "📌 *Templates (lançamentos recorrentes):*\n"
        "`template: nome - descrição - valor - Grupo - Subgrupo`\n"
        "_(opcional: `- cartao: nome`)_\n"
        "Ex: `template: aluguel - aluguel ap - 1500 - Moradia - Aluguel`\n"
        "Usar: `aluguel` (cria lançamento com data de hoje)\n"
        "Listar: `templates` | Remover: `remove template: aluguel`\n\n"
        "⏰ *Lembretes (contas fixas mensais):*\n"
        "`lembrete: template - dia N` (aviso 2 dias antes)\n"
        "`lembrete: template - dia N - auto` (lança automaticamente no dia)\n"
        "Ex: `lembrete: aluguel - dia 5` ou `lembrete: academia - dia 1 - auto`\n"
        "Confirmar: `lançar template` | Listar: `lembretes` | Remover: `remove lembrete: template`\n\n"
        "💳 *Relatório por cartão:*\n"
        "`cartao: nome` ou `cartao: nome - mes: MM/AA`\n\n"
        "📊 *Resumo:*\n"
        "`resumo` · `resumo: Grupo` · `resumo: MM/AA`\n\n"
        "🕐 *Últimos lançamentos:*\n"
        "`ultimos: N` _(máx. 20)_\n\n"
        "🗑️ *Cancelar lançamento:*\n"
        "`cancela: ID`"
    )


async def calcular_historico(
    grupo_id: int,
    subgrupo_id: int | None,
    db: AsyncSession,
    n_meses: int = 3,
) -> list[HistoricoMesDTO]:
    """
    Calcula histórico de gasto dos últimos N meses para um grupo ou subgrupo.

    Retorna lista de HistoricoMesDTO em ordem cronológica (mês mais antigo primeiro).
    Marca o mês atual com em_andamento=True.
    Inclui meses sem lançamento como gasto=0.
    """

    # Calcula data inicial (N meses atrás)
    hoje = date.today()
    mes_inicio = hoje.month - n_meses + 1
    ano_inicio = hoje.year
    if mes_inicio <= 0:
        ano_inicio -= 1
        mes_inicio += 12

    # Monta lista de meses a consultar
    historico_dict: dict[tuple[int, int], HistoricoMesDTO] = {}
    mes_atual = (hoje.month, hoje.year)
    current_mes = mes_inicio
    current_ano = ano_inicio
    for _ in range(n_meses):
        em_andamento = (current_mes == hoje.month and current_ano == hoje.year)
        historico_dict[(current_mes, current_ano)] = HistoricoMesDTO(
            mes=current_mes,
            ano=current_ano,
            gasto=Decimal("0"),
            orcamento=Decimal("0"),
            percentual=None,
            em_andamento=em_andamento,
        )
        # Próximo mês
        current_mes += 1
        if current_mes > 12:
            current_mes = 1
            current_ano += 1

    # Consulta gastos por mês
    if subgrupo_id is not None:
        # Por subgrupo específico
        resultado = await db.execute(
            select(
                extract("month", Lancamento.data_pagamento),
                extract("year", Lancamento.data_pagamento),
                func.coalesce(func.sum(Lancamento.valor), Decimal("0")),
            )
            .where(
                Lancamento.subgrupo_id == subgrupo_id,
            )
            .group_by(
                extract("month", Lancamento.data_pagamento),
                extract("year", Lancamento.data_pagamento),
            )
        )
    else:
        # Por grupo inteiro (soma todos os subgrupos)
        resultado = await db.execute(
            select(
                extract("month", Lancamento.data_pagamento),
                extract("year", Lancamento.data_pagamento),
                func.coalesce(func.sum(Lancamento.valor), Decimal("0")),
            )
            .join(Subgrupo, Lancamento.subgrupo_id == Subgrupo.id)
            .where(
                Subgrupo.grupo_id == grupo_id,
            )
            .group_by(
                extract("month", Lancamento.data_pagamento),
                extract("year", Lancamento.data_pagamento),
            )
        )

    gastos_por_mes: dict[tuple[int, int], Decimal] = {}
    for row in resultado:
        mes, ano, gasto = row
        gastos_por_mes[(int(mes), int(ano))] = Decimal(str(gasto))

    # Atualiza histórico com gastos reais
    for (mes, ano), historico_mes in historico_dict.items():
        gasto = gastos_por_mes.get((mes, ano), Decimal("0"))
        historico_mes.gasto = gasto

    # Calcula orçamento vigente (não histórico, mas vigente)
    if subgrupo_id is not None:
        subgrupo = await db.scalar(select(Subgrupo).where(Subgrupo.id == subgrupo_id))
        orcamento_vigente = subgrupo.orcamento_mensal if subgrupo else Decimal("0")
    else:
        resultado_orcamento = await db.execute(
            select(func.coalesce(func.sum(Subgrupo.orcamento_mensal), Decimal("0")))
            .where(Subgrupo.grupo_id == grupo_id)
        )
        orcamento_vigente = resultado_orcamento.scalar() or Decimal("0")

    # Atualiza orçamento e percentual em todos os meses
    for historico_mes in historico_dict.values():
        historico_mes.orcamento = orcamento_vigente
        if orcamento_vigente > 0:
            historico_mes.percentual = (
                historico_mes.gasto / orcamento_vigente * 100
            ).quantize(Decimal("1"))

    # Retorna em ordem cronológica
    return sorted(historico_dict.values(), key=lambda x: (x.ano, x.mes))


async def calcular_projecao(mes: int, ano: int, db: AsyncSession) -> ProjecaoDTO | None:
    """
    Calcula projeção de gasto até o fim do mês.

    Cálculo:
    - dias_passados = COUNT(DISTINCT data_pagamento) no mês com lançamentos
    - Se dias_passados = 0 → retorna None (bloco omitido)
    - total_gasto = SUM(valor) de todos os lançamentos do mês
    - ritmo = total_gasto / dias_passados
    - dias_no_mes = quantidade de dias do mês (28/29/30/31)
    - projecao = ritmo * dias_no_mes
    - orcamento_total = SUM(subgrupos.orcamento_mensal)
    - margem = orcamento_total - projecao

    Alertas:
    - projecao > 90% orcamento → "⚠️"
    - projecao > 100% orcamento → "🚨"
    """
    # Total de dias no mês
    _, dias_no_mes = monthrange(ano, mes)

    # Calcula total gasto e dias com lançamentos
    resultado = await db.execute(
        select(
            func.coalesce(func.sum(Lancamento.valor), Decimal("0")),
            func.count(func.distinct(Lancamento.data_pagamento))
        )
        .where(
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
    )
    row = resultado.first()

    if not row:
        total_gasto = Decimal("0")
        dias_passados = 0
    else:
        total_gasto, dias_passados = row
        dias_passados = int(dias_passados) if dias_passados else 0

    # Se não há lançamentos, omite bloco
    if dias_passados == 0:
        return None

    # Calcula ritmo e projeção
    ritmo_diario = Decimal(str(total_gasto)) / Decimal(dias_passados)
    projecao_fim_mes = ritmo_diario * Decimal(dias_no_mes)

    # Calcula orçamento total (soma de todos os subgrupos)
    resultado_orcamento = await db.execute(
        select(func.coalesce(func.sum(Subgrupo.orcamento_mensal), Decimal("0")))
    )
    orcamento_total = Decimal(str(resultado_orcamento.scalar()))

    # Calcula margem
    margem = orcamento_total - projecao_fim_mes

    # Define alerta
    alerta = None
    if orcamento_total > 0:
        percentual_projecao = (projecao_fim_mes / orcamento_total * 100).quantize(Decimal("1"))
        if percentual_projecao >= 100:
            alerta = "🚨"
        elif percentual_projecao >= 90:
            alerta = "⚠️"

    return ProjecaoDTO(
        ritmo_diario=ritmo_diario.quantize(Decimal("0.01")),
        projecao_fim_mes=projecao_fim_mes.quantize(Decimal("0.01")),
        orcamento_total=orcamento_total.quantize(Decimal("0.01")),
        margem=margem.quantize(Decimal("0.01")),
        alerta=alerta,
    )


def formatar_resumo_todos(resumos: list[ResumoDTO], mes: int, ano: int) -> str:
    cabecalho = f"📊 *Resumo — {_MESES[mes - 1]}/{str(ano)[2:]}*\n"
    if not resumos:
        return cabecalho + "Nenhum gasto registrado neste período."
    linhas = [cabecalho]
    for r in resumos:
        gasto_fmt = _fmt(r.total_gasto)
        if r.tem_orcamento:
            pct = r.percentual
            orcamento_fmt = _fmt(r.orcamento_mensal)
            alerta = " 🚨" if r.alerta == "estourado" else " ⚠️" if r.alerta == "aviso" else ""
            linhas.append(f"*{r.grupo_nome}:* R$ {gasto_fmt} / R$ {orcamento_fmt} ({pct}%){alerta}")
        else:
            linhas.append(f"*{r.grupo_nome}:* R$ {gasto_fmt}")
    return "\n".join(linhas)


def formatar_resumo_subgrupos(resumo: ResumoSubgrupoDTO, mes: int, ano: int) -> str:
    linhas = [f"📊 *{resumo.grupo_nome} — {_MESES[mes - 1]}/{str(ano)[2:]}*\n"]
    for subgrupo, valor in resumo.por_subgrupo:
        linhas.append(f"  • {subgrupo}: R$ {_fmt(valor)}")
    linhas.append(f"\n*Total: R$ {_fmt(resumo.total_gasto)}*")
    if resumo.orcamento_mensal > 0:
        pct = (resumo.total_gasto / resumo.orcamento_mensal * 100).quantize(Decimal("1"))
        orcamento_fmt = _fmt(resumo.orcamento_mensal)
        linhas.append(f"📊 Orçamento: R$ {orcamento_fmt} ({pct}%)")
        if pct >= 100:
            linhas.append("🚨 Orçamento estourado!")
        elif pct >= 80:
            linhas.append(f"⚠️ Atenção: {pct}% do orçamento utilizado")
    return "\n".join(linhas)


def formatar_relatorio_cartao(dto: ResumoCartaoDTO) -> str:
    linhas = [f"💳 *{dto.cartao.title()} — {_MESES[dto.mes - 1]}/{str(dto.ano)[2:]}*\n"]
    for grupo_nome, valor in dto.por_grupo:
        linhas.append(f"  • {grupo_nome}: R$ {_fmt(valor)}")
    linhas.append(f"\n*Total: R$ {_fmt(dto.total)}*")
    return "\n".join(linhas)


def formatar_cartao_nao_encontrado(cartao: str) -> str:
    return f"❌ Nenhum lançamento encontrado para o cartão *{cartao}*."


def formatar_ultimos(lancamentos: list[tuple]) -> str:
    if not lancamentos:
        return "📭 Nenhum lançamento encontrado."
    linhas = ["📋 *Últimos lançamentos:*\n"]
    for lancamento, grupo_nome in lancamentos:
        data = lancamento.data_gasto.strftime("%d/%m/%y")
        cartao_str = f" | 💳 {lancamento.cartao}" if lancamento.cartao else ""
        linhas.append(
            f"*#{lancamento.id}* — {data} — {lancamento.descricao}\n"
            f"   R$ {_fmt(lancamento.valor)} | {grupo_nome}/{lancamento.subgrupo.nome}{cartao_str}"
        )
    return "\n".join(linhas)


def formatar_cancela_sucesso(info: LancamentoInfo, novo_resumo: ResumoDTO) -> str:
    data = info.data_gasto.strftime("%d/%m/%y")
    linhas = [
        f"✅ Lançamento #{info.id} cancelado!",
        f"📌 {info.descricao} — R$ {_fmt(info.valor)} ({data})",
    ]
    gasto_fmt = _fmt(novo_resumo.total_gasto)
    linhas.append(f"📂 {info.grupo_nome}: R$ {gasto_fmt} gastos este mês")
    if novo_resumo.tem_orcamento:
        pct = novo_resumo.percentual
        orcamento_fmt = _fmt(novo_resumo.orcamento_mensal)
        restante_fmt = _fmt(novo_resumo.restante)
        linhas.append(f"📊 Orçamento: R$ {orcamento_fmt} | Gasto: R$ {gasto_fmt} | Restante: R$ {restante_fmt} ({pct}%)")
    return "\n".join(linhas)


def formatar_cancela_nao_encontrado(lancamento_id: int) -> str:
    return f"❌ Lançamento #{lancamento_id} não encontrado."


def formatar_projecao(projecao: ProjecaoDTO, mes: int, ano: int) -> str:
    """Formata bloco de projeção para anexar ao resumo."""
    linhas = [
        f"📈 *Projeção para {_MESES[mes - 1]}/{str(ano)[2:]}:*",
        f"• Ritmo atual: R$ {_fmt(projecao.ritmo_diario)}/dia",
        f"• Estimativa fim do mês: R$ {_fmt(projecao.projecao_fim_mes)}",
    ]

    # Só exibe margem se há orçamento total
    if projecao.orcamento_total > 0:
        linhas.append(f"• Orçamento total: R$ {_fmt(projecao.orcamento_total)} | Margem restante: R$ {_fmt(projecao.margem)}")

    # Adiciona alerta se houver
    if projecao.alerta:
        if projecao.alerta == "🚨":
            linhas.append(f"🚨 *Projeção indica estouro do orçamento*")
        elif projecao.alerta == "⚠️":
            linhas.append(f"⚠️ *Projeção indica orçamento apertado*")

    return "\n".join(linhas)


def formatar_historico(
    historico: list[HistoricoMesDTO],
    grupo_nome: str,
    subgrupo_nome: str | None = None,
) -> str:
    """
    Formata lista de HistoricoMesDTO em mensagem legível.

    Exemplo (por subgrupo):
    📈 Histórico — Alimentação > Mercado
    • mar/26: R$ 380,00 / R$ 400,00 (95%) ⚠️
    • abr/26: R$ 290,00 / R$ 400,00 (72%) ✅
    • mai/26: R$ 210,00 / R$ 400,00 (52%) ✅ ← em andamento
    """
    titulo = f"📈 Histórico — {grupo_nome}"
    if subgrupo_nome:
        titulo += f" > {subgrupo_nome}"

    linhas = [f"{titulo}\n"]

    for mes_dto in historico:
        mes_nome = _MESES[mes_dto.mes - 1]
        ano_fmt = str(mes_dto.ano)[2:]  # Ex: 26
        gasto_fmt = _fmt(mes_dto.gasto)

        # Linha base: mês + gasto
        linha = f"• {mes_nome.lower()}/{ano_fmt}: R$ {gasto_fmt}"

        # Adiciona orçamento e percentual se houver
        if mes_dto.orcamento > 0:
            orcamento_fmt = _fmt(mes_dto.orcamento)
            pct = mes_dto.percentual
            alerta = ""
            if pct is not None:
                if pct >= 100:
                    alerta = " 🚨"
                elif pct >= 80:
                    alerta = " ⚠️"
                else:
                    alerta = " ✅"
            linha += f" / R$ {orcamento_fmt} ({pct}%){alerta}"
        else:
            linha += " ✅"

        # Marca mês em andamento
        if mes_dto.em_andamento:
            linha += " ← em andamento"

        linhas.append(linha)

    return "\n".join(linhas)


async def calcular_resumo_periodo(data_inicio: date, data_fim: date, db: AsyncSession) -> list[ResumoPeriodoGrupoDTO] | None:
    resultado = await db.execute(
        select(
            Grupo.nome,
            Subgrupo.nome,
            func.sum(Lancamento.valor)
        )
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .join(Subgrupo, Lancamento.subgrupo_id == Subgrupo.id)
        .where(
            Lancamento.data_pagamento >= data_inicio,
            Lancamento.data_pagamento <= data_fim,
        )
        .group_by(Grupo.id, Grupo.nome, Subgrupo.id, Subgrupo.nome)
        .order_by(Grupo.nome, Subgrupo.nome)
    )
    rows = resultado.all()
    if not rows:
        return None

    grupos_dict: dict[str, list[tuple[str, Decimal]]] = {}
    for grupo_nome, subgrupo_nome, valor in rows:
        if grupo_nome not in grupos_dict:
            grupos_dict[grupo_nome] = []
        grupos_dict[grupo_nome].append((subgrupo_nome, Decimal(str(valor))))

    grupos = []
    for grupo_nome in sorted(grupos_dict.keys()):
        subgrupos = grupos_dict[grupo_nome]
        total_grupo = sum(v for _, v in subgrupos)
        grupos.append(
            ResumoPeriodoGrupoDTO(
                grupo_nome=grupo_nome,
                por_subgrupo=subgrupos,
                total_grupo=total_grupo,
            )
        )

    return grupos


def formatar_resumo_periodo(grupos: list[ResumoPeriodoGrupoDTO], data_inicio: date, data_fim: date) -> str:
    inicio_fmt = data_inicio.strftime("%d/%m/%y").lstrip("0").replace("/0", "/")
    fim_fmt = data_fim.strftime("%d/%m/%y").lstrip("0").replace("/0", "/")

    linhas = [f"📊 Resumo: {inicio_fmt} a {fim_fmt}\n"]

    total_geral = Decimal("0")
    for grupo in grupos:
        linhas.append(f"📂 {grupo.grupo_nome}")
        for subgrupo_nome, valor in grupo.por_subgrupo:
            linhas.append(f"  └ {subgrupo_nome}: R$ {_fmt(valor)}")
        linhas.append(f"  Total: R$ {_fmt(grupo.total_grupo)}\n")
        total_geral += grupo.total_grupo

    linhas.append(f"💰 Total do período: R$ {_fmt(total_geral)}")
    return "\n".join(linhas)


def _fmt(valor: Decimal) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def calcular_comparativo(mes_atual: int, ano_atual: int, db: AsyncSession) -> "ComparativoDTO":
    """
    Calcula comparativo entre mês atual (M-1) vs mês anterior (M-2).
    Por exemplo, no dia 1/06, compara mai (05) vs abr (04).
    """
    from app.schemas import ComparativoDTO, ComparativoGrupoDTO

    # Calcula mês e ano anterior
    if mes_atual == 1:
        mes_anterior = 12
        ano_anterior = ano_atual - 1
    else:
        mes_anterior = mes_atual - 1
        ano_anterior = ano_atual

    # Busca todos os grupos com lançamentos no mês atual
    resultado_atual = await db.execute(
        select(
            Grupo.id,
            Grupo.nome,
            func.coalesce(func.sum(Lancamento.valor), Decimal("0"))
        )
        .join(Lancamento, Grupo.id == Lancamento.grupo_id, isouter=True)
        .where(
            extract("month", Lancamento.data_pagamento) == mes_atual,
            extract("year", Lancamento.data_pagamento) == ano_atual,
        )
        .group_by(Grupo.id, Grupo.nome)
    )
    grupos_atuais = resultado_atual.all()

    # Dicionário com gastos do mês anterior para todos os grupos
    resultado_anterior = await db.execute(
        select(
            Grupo.id,
            func.coalesce(func.sum(Lancamento.valor), Decimal("0"))
        )
        .join(Lancamento, Grupo.id == Lancamento.grupo_id, isouter=True)
        .where(
            extract("month", Lancamento.data_pagamento) == mes_anterior,
            extract("year", Lancamento.data_pagamento) == ano_anterior,
        )
        .group_by(Grupo.id)
    )
    gastos_anteriores = {grupo_id: Decimal(str(valor)) for grupo_id, valor in resultado_anterior.all()}

    # Monta lista de grupos a comparar
    # Critério: inclui grupos que têm gasto em pelo menos um dos dois meses
    grupos_ids = set(g[0] for g in grupos_atuais) | set(gastos_anteriores.keys())

    grupos_comparativo = []
    total_gasto_atual = Decimal("0")
    total_orcamento_atual = Decimal("0")
    total_gasto_anterior = Decimal("0")

    for grupo_id in sorted(grupos_ids):
        # Busca dados do grupo
        grupo = await db.scalar(select(Grupo).where(Grupo.id == grupo_id))
        if not grupo:
            continue

        # Gasto no mês atual
        gasto_atual_row = next((g for g in grupos_atuais if g[0] == grupo_id), None)
        gasto_atual = Decimal(str(gasto_atual_row[2])) if gasto_atual_row else Decimal("0")

        # Gasto no mês anterior
        gasto_anterior = gastos_anteriores.get(grupo_id, Decimal("0"))

        # Orçamento atual (soma dos subgrupos)
        resultado_orcamento = await db.execute(
            select(func.coalesce(func.sum(Subgrupo.orcamento_mensal), Decimal("0")))
            .where(Subgrupo.grupo_id == grupo_id)
        )
        orcamento = resultado_orcamento.scalar()

        # Acumula totais
        total_gasto_atual += gasto_atual
        total_orcamento_atual += orcamento
        total_gasto_anterior += gasto_anterior

        # Calcula deltas
        delta_valor = gasto_atual - gasto_anterior
        if gasto_anterior > 0:
            delta_percentual = (delta_valor / gasto_anterior * 100).quantize(Decimal("0.1"))
        else:
            delta_percentual = None  # Novo no mês (sem gasto anterior)

        # Calcula percentual de orçamento
        if orcamento > 0:
            percentual_orcamento = (gasto_atual / orcamento * 100).quantize(Decimal("1"))
        else:
            percentual_orcamento = None

        # Omite grupos sem gasto em nenhum dos dois meses
        if gasto_atual > 0 or gasto_anterior > 0:
            grupos_comparativo.append(
                ComparativoGrupoDTO(
                    grupo_nome=grupo.nome,
                    gasto_mes_atual=gasto_atual.quantize(Decimal("0.01")),
                    orcamento_mes_atual=orcamento.quantize(Decimal("0.01")),
                    gasto_mes_anterior=gasto_anterior if gasto_anterior > 0 else None,
                    delta_valor=delta_valor.quantize(Decimal("0.01")),
                    delta_percentual=delta_percentual,
                    percentual_orcamento=percentual_orcamento,
                )
            )

    # Calcula delta total
    delta_total_valor = total_gasto_atual - total_gasto_anterior
    if total_gasto_anterior > 0:
        delta_total_percentual = (delta_total_valor / total_gasto_anterior * 100).quantize(Decimal("0.1"))
    else:
        delta_total_percentual = None

    return ComparativoDTO(
        mes_atual=mes_atual,
        ano_atual=ano_atual,
        mes_anterior=mes_anterior,
        ano_anterior=ano_anterior,
        grupos=grupos_comparativo,
        total_gasto_atual=total_gasto_atual.quantize(Decimal("0.01")),
        total_orcamento_atual=total_orcamento_atual.quantize(Decimal("0.01")),
        total_gasto_anterior=total_gasto_anterior.quantize(Decimal("0.01")),
        delta_total_valor=delta_total_valor.quantize(Decimal("0.01")),
        delta_total_percentual=delta_total_percentual,
    )


def formatar_comparativo(comparativo: "ComparativoDTO") -> str:
    """
    Formata o comparativo para exibição no WhatsApp.
    Mostra gasto, orçamento e variação vs mês anterior.
    """
    from app.schemas import ComparativoDTO

    mes_nome_atual = _MESES[comparativo.mes_atual - 1]
    ano_str = str(comparativo.ano_atual)[2:]

    linhas = [f"📊 *Fechamento de {mes_nome_atual}/{ano_str}*\n"]

    for grupo in comparativo.grupos:
        linhas.append(f"📂 *{grupo.grupo_nome}*")

        # Linha 1: gasto, orçamento e percentual
        gasto_fmt = _fmt(grupo.gasto_mes_atual)
        if grupo.orcamento_mes_atual > 0:
            pct = grupo.percentual_orcamento
            orcamento_fmt = _fmt(grupo.orcamento_mes_atual)
            alerta = " 🚨" if pct and pct >= 100 else " ✅"
            linhas.append(f"  Gasto: R$ {gasto_fmt} | Orçamento: R$ {orcamento_fmt} ({pct}%){alerta}")
        else:
            linhas.append(f"  Gasto: R$ {gasto_fmt}")

        # Linha 2: comparação vs mês anterior
        if grupo.gasto_mes_anterior is not None:
            gasto_anterior_fmt = _fmt(grupo.gasto_mes_anterior)
            delta_fmt = _fmt(grupo.delta_valor)
            delta_pct = grupo.delta_percentual

            # Define ícone de variação
            if delta_pct is None or delta_pct == 0:
                icone = "➡️"
            elif abs(delta_pct) < 5:
                icone = "➡️"
            elif grupo.delta_valor > 0:
                icone = "⬆️"
            else:
                icone = "⬇️"

            delta_sinal = "+" if grupo.delta_valor > 0 else ""
            if delta_pct is not None:
                linhas.append(f"  vs {_MESES[comparativo.mes_anterior - 1]}: R$ {gasto_anterior_fmt} → {delta_sinal}R$ {delta_fmt} ({delta_sinal}{delta_pct}%) {icone}")
            else:
                linhas.append(f"  vs {_MESES[comparativo.mes_anterior - 1]}: R$ {gasto_anterior_fmt} → {delta_sinal}R$ {delta_fmt} {icone}")
        else:
            # Novo no mês (sem gasto anterior)
            linhas.append(f"  vs {_MESES[comparativo.mes_anterior - 1]}: novo neste mês")

        linhas.append("")

    # Total consolidado
    linhas.append(f"💰 *Total gasto:* R$ {_fmt(comparativo.total_gasto_atual)} | *Orçamento total:* R$ {_fmt(comparativo.total_orcamento_atual)}")
    if comparativo.total_orcamento_atual > 0:
        pct_total = (comparativo.total_gasto_atual / comparativo.total_orcamento_atual * 100).quantize(Decimal("1"))
        linhas.append(f"  Utilização: {pct_total}%")

    # Delta total
    if comparativo.total_gasto_anterior > 0:
        delta_fmt = _fmt(comparativo.delta_total_valor)
        delta_pct = comparativo.delta_total_percentual
        delta_sinal = "+" if comparativo.delta_total_valor > 0 else ""

        if delta_pct is not None and abs(delta_pct) < 5:
            icone = "➡️"
        elif comparativo.delta_total_valor > 0:
            icone = "⬆️"
        else:
            icone = "⬇️"

        if delta_pct is not None:
            linhas.append(f"  vs {_MESES[comparativo.mes_anterior - 1]}: {delta_sinal}R$ {delta_fmt} ({delta_sinal}{delta_pct}%) {icone}")
        else:
            linhas.append(f"  vs {_MESES[comparativo.mes_anterior - 1]}: {delta_sinal}R$ {delta_fmt} {icone}")

    return "\n".join(linhas)


def formatar_resumo_parcelas(resumo: ResumoDTO, lancamentos: list, dto) -> str:
    valor_total_fmt = _fmt(dto.valor)
    valor_parcela_fmt = _fmt(dto.valor / dto.parcelas)
    mes_inicio_fmt = f"{dto.inicio_parcela.month:02d}/{str(dto.inicio_parcela.year)[2:]}"

    data_fim = dto.inicio_parcela
    for _ in range(1, dto.parcelas):
        mes = data_fim.month + 1
        ano = data_fim.year
        if mes > 12:
            mes = 1
            ano += 1
        data_fim = date(ano, mes, 1)
    mes_fim_fmt = f"{data_fim.month:02d}/{str(data_fim.year)[2:]}"

    gasto_fmt = _fmt(resumo.total_gasto)
    linhas = [
        f"✅ {dto.parcelas} parcelas salvas!",
        f"📦 {dto.descricao} — R$ {valor_total_fmt} em {dto.parcelas}x de R$ {valor_parcela_fmt}",
        f"📅 Primeira parcela: {mes_inicio_fmt} | Última: {mes_fim_fmt}",
        f"📂 {resumo.grupo_nome}: R$ {gasto_fmt} gastos em {mes_inicio_fmt}",
    ]
    if resumo.tem_orcamento:
        pct = resumo.percentual
        orcamento_fmt = _fmt(resumo.orcamento_mensal)
        restante_fmt = _fmt(resumo.restante)
        linhas.append(f"📊 Orçamento: R$ {orcamento_fmt} | Gasto: R$ {gasto_fmt} | Restante: R$ {restante_fmt} ({pct}%)")
        if resumo.alerta == "estourado":
            linhas.append("🚨 Orçamento estourado!")
        elif resumo.alerta == "aviso":
            linhas.append(f"⚠️ Atenção: {pct}% do orçamento utilizado")
    return "\n".join(linhas)
