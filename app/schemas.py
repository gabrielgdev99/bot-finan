from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class LancamentoDTO:
    data_gasto: date
    descricao: str
    valor: Decimal
    grupo: str
    subgrupo: str
    data_pagamento: date
    cartao: str | None = None
    texto_original: str = field(default="", repr=False)
    parcelas: int = 1
    inicio_parcela: date | None = None


@dataclass
class OrcamentoDTO:
    grupo: str
    subgrupo: str
    valor: Decimal
    mes: date | None = None


@dataclass
class RelatorioCartaoDTO:
    cartao: str
    mes: int | None = None
    ano: int | None = None


@dataclass
class ResumoComandoDTO:
    grupo: str | None = None
    mes: int | None = None
    ano: int | None = None


@dataclass
class UltimosDTO:
    n: int


@dataclass
class CancelaDTO:
    lancamento_id: int


@dataclass
class LancamentoInfo:
    id: int
    descricao: str
    valor: Decimal
    data_gasto: date
    grupo_nome: str


@dataclass
class ProjecaoDTO:
    ritmo_diario: Decimal
    projecao_fim_mes: Decimal
    orcamento_total: Decimal
    margem: Decimal
    alerta: str | None = None


@dataclass
class HistoricoMesDTO:
    mes: int
    ano: int
    gasto: Decimal
    orcamento: Decimal
    percentual: Decimal | None
    em_andamento: bool


@dataclass
class HistoricoComandoDTO:
    grupo: str | None = None
    subgrupo: str | None = None


@dataclass
class ComparativoGrupoDTO:
    grupo_nome: str
    gasto_mes_atual: Decimal
    orcamento_mes_atual: Decimal
    gasto_mes_anterior: Decimal | None  # None se não houve gasto no mês anterior
    delta_valor: Decimal  # gasto_atual - gasto_anterior
    delta_percentual: Decimal | None  # (delta / gasto_anterior) * 100 se houver anterior
    percentual_orcamento: Decimal | None  # (gasto_atual / orcamento) * 100 se orcamento > 0


@dataclass
class ComparativoDTO:
    mes_atual: int
    ano_atual: int
    mes_anterior: int
    ano_anterior: int
    grupos: list[ComparativoGrupoDTO]
    total_gasto_atual: Decimal
    total_orcamento_atual: Decimal
    total_gasto_anterior: Decimal
    delta_total_valor: Decimal
    delta_total_percentual: Decimal | None


@dataclass
class TemplateDTO:
    nome: str
    descricao: str
    valor: Decimal
    grupo: str
    subgrupo: str
    cartao: str | None = None


@dataclass
class RemoveTemplateDTO:
    nome: str


@dataclass
class ResumoPeriodoDTO:
    data_inicio: date
    data_fim: date


@dataclass
class ResumoPeriodoGrupoDTO:
    grupo_nome: str
    por_subgrupo: list[tuple[str, Decimal]]
    total_grupo: Decimal


@dataclass
class AliasDTO:
    palavra_chave: str
    grupo: str
    subgrupo: str


@dataclass
class RemoveAliasDTO:
    palavra_chave: str


@dataclass
class AliasInfoDTO:
    palavra_chave: str
    grupo_nome: str
    subgrupo_nome: str


@dataclass
class LembreteDTO:
    template_nome: str
    dia_vencimento: int
    auto: bool = False


@dataclass
class RemoveLembreteDTO:
    template_nome: str


@dataclass
class LancarTemplateDTO:
    template_nome: str
