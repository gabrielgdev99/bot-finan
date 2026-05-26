import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.schemas import CancelaDTO, HistoricoComandoDTO, LancamentoDTO, OrcamentoDTO, RelatorioCartaoDTO, ResumoComandoDTO, TemplateDTO, RemoveTemplateDTO, UltimosDTO

_ORCAMENTO_RE = re.compile(
    r"^or[cç]amento:\s*(.+?)\s*-\s*(.+?)\s*-\s*([\d]+(?:[.,]\d+)?)\s*$",
    re.IGNORECASE,
)
_CARTAO_CMD_RE = re.compile(
    r"^cart[aã]o:\s*(.+?)(?:\s*-\s*mes:\s*(\d{2}/\d{2}))?\s*$",
    re.IGNORECASE,
)
_RESUMO_CMD_RE = re.compile(r"^resumo(?::\s*(.+))?\s*$", re.IGNORECASE)
_HISTORICO_CMD_RE = re.compile(r"^historico:\s*(.+)$", re.IGNORECASE)
_MES_ANO_RE = re.compile(r"^(\d{2})/(\d{2})$")
_ULTIMOS_RE = re.compile(r"^ultimos:\s*(\d+)\s*$", re.IGNORECASE)
_CANCELA_RE = re.compile(r"^cancela:\s*(\d+)\s*$", re.IGNORECASE)
_TEMPLATE_RE = re.compile(
    r"^template:\s*(.+?)\s*-\s*(.+?)\s*-\s*([\d]+(?:[.,]\d+)?)\s*-\s*(.+?)\s*-\s*(.+?)(?:\s*-\s*cartao:\s*(.+))?\s*$",
    re.IGNORECASE,
)
_REMOVE_TEMPLATE_RE = re.compile(r"^remove\s+template:\s*(.+?)\s*$", re.IGNORECASE)

_CAMPO_RE = re.compile(r"^([\w\s]+):\s*(.+)$")


def parse_lancamento(texto: str) -> LancamentoDTO | None:
    partes = [p.strip() for p in texto.strip().split(" - ")]

    if len(partes) < 5:
        return None

    data_gasto = _parse_data_gasto(partes[0])
    if data_gasto is None:
        return None

    descricao = partes[1]
    if not descricao:
        return None

    valor = _parse_decimal(partes[2])
    if valor is None or valor <= 0:
        return None

    grupo = partes[3]
    if not grupo or ":" in grupo:
        return None

    subgrupo = partes[4]
    if not subgrupo or ":" in subgrupo:
        return None

    campos = _extrair_campos(partes[5:])

    cartao = campos.get("cartao") or campos.get("cartão")
    data_pagamento = _parse_data_pagamento(campos.get("pagamento"), data_gasto) or data_gasto

    return LancamentoDTO(
        data_gasto=data_gasto,
        descricao=descricao,
        valor=valor,
        grupo=grupo,
        subgrupo=subgrupo,
        cartao=cartao,
        data_pagamento=data_pagamento,
        texto_original=texto.strip(),
    )


def parse_ajuda(texto: str) -> bool:
    return texto.strip().lower() in ("ajuda", "help", "?")


def parse_relatorio_cartao(texto: str) -> RelatorioCartaoDTO | None:
    match = _CARTAO_CMD_RE.match(texto.strip())
    if not match:
        return None
    cartao = match.group(1).strip()
    mes_str = match.group(2)
    if mes_str:
        m = _MES_ANO_RE.match(mes_str.strip())
        if m:
            return RelatorioCartaoDTO(cartao=cartao, mes=int(m.group(1)), ano=2000 + int(m.group(2)))
    return RelatorioCartaoDTO(cartao=cartao)


def parse_resumo_comando(texto: str) -> ResumoComandoDTO | None:
    match = _RESUMO_CMD_RE.match(texto.strip())
    if not match:
        return None
    arg = match.group(1)
    if arg is None:
        return ResumoComandoDTO()
    arg = arg.strip()
    m = _MES_ANO_RE.match(arg)
    if m:
        return ResumoComandoDTO(mes=int(m.group(1)), ano=2000 + int(m.group(2)))
    return ResumoComandoDTO(grupo=arg)


def parse_ultimos(texto: str) -> UltimosDTO | None:
    match = _ULTIMOS_RE.match(texto.strip())
    if not match:
        return None
    n = int(match.group(1))
    if n < 1:
        return None
    return UltimosDTO(n=n)


def parse_cancela(texto: str) -> CancelaDTO | None:
    match = _CANCELA_RE.match(texto.strip())
    if not match:
        return None
    return CancelaDTO(lancamento_id=int(match.group(1)))


def parse_orcamento(texto: str) -> OrcamentoDTO | None:
    match = _ORCAMENTO_RE.match(texto.strip())
    if not match:
        return None

    grupo = match.group(1).strip()
    subgrupo = match.group(2).strip()
    valor = _parse_decimal(match.group(3))
    if valor is None or valor < 0:
        return None

    return OrcamentoDTO(grupo=grupo, subgrupo=subgrupo, valor=valor)


def parse_template(texto: str) -> TemplateDTO | None:
    match = _TEMPLATE_RE.match(texto.strip())
    if not match:
        return None

    nome = match.group(1).strip()
    descricao = match.group(2).strip()
    valor = _parse_decimal(match.group(3))
    grupo = match.group(4).strip()
    subgrupo = match.group(5).strip()
    cartao = match.group(6).strip() if match.group(6) else None

    if not nome or not descricao or valor is None or valor <= 0 or not grupo or not subgrupo:
        return None
    if ":" in grupo or ":" in subgrupo:
        return None

    return TemplateDTO(
        nome=nome,
        descricao=descricao,
        valor=valor,
        grupo=grupo,
        subgrupo=subgrupo,
        cartao=cartao,
    )


def parse_remove_template(texto: str) -> RemoveTemplateDTO | None:
    match = _REMOVE_TEMPLATE_RE.match(texto.strip())
    if not match:
        return None
    nome = match.group(1).strip()
    if not nome:
        return None
    return RemoveTemplateDTO(nome=nome)


def parse_historico(texto: str) -> HistoricoComandoDTO | None:
    """
    Parseia comando de histórico.

    Formatos aceitos:
    - historico: Alimentação
    - historico: Alimentação > Mercado
    """
    match = _HISTORICO_CMD_RE.match(texto.strip())
    if not match:
        return None

    arg = match.group(1).strip()
    if not arg:
        return None

    # Detecta se há '>' para separar grupo e subgrupo
    if " > " in arg:
        partes = arg.split(" > ", 1)
        grupo = partes[0].strip()
        subgrupo = partes[1].strip()
        if not grupo or not subgrupo:
            return None
        return HistoricoComandoDTO(grupo=grupo, subgrupo=subgrupo)
    else:
        # Apenas grupo
        return HistoricoComandoDTO(grupo=arg)


def _parse_data_gasto(texto: str) -> date | None:
    match = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", texto.strip())
    if not match:
        return None
    dia, mes = int(match.group(1)), int(match.group(2))
    ano_str = match.group(3)
    if ano_str is None:
        ano = date.today().year
    elif len(ano_str) == 2:
        ano = 2000 + int(ano_str)
    else:
        ano = int(ano_str)
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


def _parse_data_pagamento(texto: str | None, referencia: date) -> date | None:
    if not texto:
        return None
    match = re.match(r"^(\d{2})/(\d{2})$", texto.strip())
    if not match:
        return None
    dia, mes = int(match.group(1)), int(match.group(2))
    ano = referencia.year if mes >= referencia.month else referencia.year + 1
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


def _parse_decimal(texto: str) -> Decimal | None:
    try:
        return Decimal(texto.strip().replace(",", "."))
    except InvalidOperation:
        return None


def _extrair_campos(partes: list[str]) -> dict[str, str]:
    campos: dict[str, str] = {}
    for parte in partes:
        match = _CAMPO_RE.match(parte.strip())
        if match:
            chave = match.group(1).strip().lower()
            valor = match.group(2).strip()
            campos[chave] = valor
    return campos
