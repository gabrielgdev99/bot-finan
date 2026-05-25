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


@dataclass
class OrcamentoDTO:
    grupo: str
    valor: Decimal


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
