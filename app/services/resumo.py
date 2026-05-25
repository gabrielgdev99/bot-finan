from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grupo import Grupo
from app.models.lancamento import Lancamento
from app.schemas import LancamentoInfo

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


async def calcular_resumo(grupo_nome: str, mes: int, ano: int, db: AsyncSession) -> ResumoDTO:
    resultado = await db.execute(
        select(func.coalesce(func.sum(Lancamento.valor), Decimal("0")), Grupo.orcamento_mensal)
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .where(
            Grupo.nome == grupo_nome,
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Grupo.orcamento_mensal)
    )
    row = resultado.first()

    if row:
        total_gasto, orcamento_mensal = row
    else:
        total_gasto = Decimal("0")
        grupo = await db.scalar(select(Grupo).where(Grupo.nome == grupo_nome))
        orcamento_mensal = grupo.orcamento_mensal if grupo else Decimal("0")

    return ResumoDTO(
        grupo_nome=grupo_nome,
        total_gasto=Decimal(str(total_gasto)),
        orcamento_mensal=Decimal(str(orcamento_mensal)),
    )


async def calcular_resumo_todos(mes: int, ano: int, db: AsyncSession) -> list[ResumoDTO]:
    resultado = await db.execute(
        select(Grupo.nome, func.coalesce(func.sum(Lancamento.valor), Decimal("0")), Grupo.orcamento_mensal)
        .join(Lancamento, Grupo.id == Lancamento.grupo_id)
        .where(
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Grupo.nome, Grupo.orcamento_mensal)
        .order_by(Grupo.nome)
    )
    return [
        ResumoDTO(
            grupo_nome=row[0],
            total_gasto=Decimal(str(row[1])),
            orcamento_mensal=Decimal(str(row[2])),
        )
        for row in resultado.all()
    ]


async def calcular_resumo_subgrupos(grupo_nome: str, mes: int, ano: int, db: AsyncSession) -> ResumoSubgrupoDTO | None:
    resultado = await db.execute(
        select(Lancamento.subgrupo, func.sum(Lancamento.valor))
        .join(Grupo, Lancamento.grupo_id == Grupo.id)
        .where(
            Grupo.nome == grupo_nome,
            extract("month", Lancamento.data_pagamento) == mes,
            extract("year", Lancamento.data_pagamento) == ano,
        )
        .group_by(Lancamento.subgrupo)
        .order_by(Lancamento.subgrupo)
    )
    rows = resultado.all()
    if not rows:
        return None

    por_subgrupo = [(row[0] or "—", Decimal(str(row[1]))) for row in rows]
    total = sum(v for _, v in por_subgrupo)

    grupo = await db.scalar(select(Grupo).where(Grupo.nome == grupo_nome))
    orcamento = grupo.orcamento_mensal if grupo else Decimal("0")

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


def formatar_confirmacao_orcamento(grupo_nome: str, valor: Decimal) -> str:
    return f'✅ Orçamento de "{grupo_nome}" definido: R$ {_fmt(valor)}/mês'


def formatar_ajuda() -> str:
    return (
        "❓ *Comandos disponíveis:*\n\n"
        "💰 *Lançamento:*\n"
        "`DD/MM/AA - descrição - valor - Grupo - Subgrupo`\n"
        "_(opcionais: `- cartao: nome` `- pagamento: DD/MM`)_\n"
        "Ex: `25/05/26 - padaria - 25 - Alimentação - Padaria`\n\n"
        "📋 *Orçamento:*\n"
        "`orçamento: grupo - valor`\n"
        "Ex: `orçamento: Alimentação - 500`\n\n"
        "💳 *Relatório por cartão:*\n"
        "`cartao: nome` ou `cartao: nome - mes: MM/AA`\n\n"
        "📊 *Resumo:*\n"
        "`resumo` · `resumo: Grupo` · `resumo: MM/AA`\n\n"
        "🕐 *Últimos lançamentos:*\n"
        "`ultimos: N` _(máx. 20)_\n\n"
        "🗑️ *Cancelar lançamento:*\n"
        "`cancela: ID`"
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
            f"   R$ {_fmt(lancamento.valor)} | {grupo_nome}/{lancamento.subgrupo}{cartao_str}"
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


def _fmt(valor: Decimal) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
