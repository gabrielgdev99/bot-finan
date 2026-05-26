import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.schemas import AliasDTO, CancelaDTO, HistoricoComandoDTO, LancamentoDTO, LancarTemplateDTO, LembreteDTO, OrcamentoDTO, RelatorioCartaoDTO, RemoveAliasDTO, RemoveLembreteDTO, ResumoComandoDTO, ResumoPeriodoDTO, RemoveTemplateDTO, TemplateDTO, UltimosDTO

_ORCAMENTO_RE = re.compile(
    r"^or[cç]amento:\s*(.+?)\s*-\s*(.+?)\s*-\s*([\d]+(?:[.,]\d+)?)(?:\s*-\s*mes:\s*(\d{2}/\d{2}))?\s*$",
    re.IGNORECASE,
)
_CARTAO_CMD_RE = re.compile(
    r"^cart[aã]o:\s*(.+?)(?:\s*-\s*mes:\s*(\d{2}/\d{2}))?\s*$",
    re.IGNORECASE,
)
_RESUMO_CMD_RE = re.compile(r"^resumo(?::\s*(.+))?\s*$", re.IGNORECASE)
_RESUMO_PERIODO_RE = re.compile(r"^resumo:\s*(\d{2}/\d{2})\s+a\s+(\d{2}/\d{2})\s*$", re.IGNORECASE)
_HISTORICO_CMD_RE = re.compile(r"^historico:\s*(.+)$", re.IGNORECASE)
_MES_ANO_RE = re.compile(r"^(\d{2})/(\d{2})$")
_ULTIMOS_RE = re.compile(r"^ultimos:\s*(\d+)\s*$", re.IGNORECASE)
_CANCELA_RE = re.compile(r"^cancela:\s*(\d+)\s*$", re.IGNORECASE)
_TEMPLATE_RE = re.compile(
    r"^template:\s*(.+?)\s*-\s*(.+?)\s*-\s*([\d]+(?:[.,]\d+)?)\s*-\s*(.+?)\s*-\s*(.+?)(?:\s*-\s*cartao:\s*(.+))?\s*$",
    re.IGNORECASE,
)
_REMOVE_TEMPLATE_RE = re.compile(r"^remove\s+template:\s*(.+?)\s*$", re.IGNORECASE)
_ALIAS_RE = re.compile(
    r"^alias:\s*(.+?)\s*(?:->|→)\s*(.+?)\s*>\s*(.+?)\s*$",
    re.IGNORECASE,
)
_REMOVE_ALIAS_RE = re.compile(r"^remove\s+alias:\s*(.+?)\s*$", re.IGNORECASE)
_LEMBRETE_RE = re.compile(
    r"^lembrete:\s*(.+?)\s*-\s*dia\s*(\d+)(?:\s*-\s*(auto))?\s*$",
    re.IGNORECASE,
)
_REMOVE_LEMBRETE_RE = re.compile(r"^remove\s+lembrete:\s*(.+?)\s*$", re.IGNORECASE)
_LANCAR_TEMPLATE_RE = re.compile(r"^lan[çc]ar\s+(.+?)\s*$", re.IGNORECASE)

_CAMPO_RE = re.compile(r"^([\w\s]+):\s*(.+)$")


def parse_lancamento(texto: str) -> LancamentoDTO | None:
    partes = [p.strip() for p in texto.strip().split(" - ")]

    if len(partes) < 3:
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

    grupo = partes[3].strip() if len(partes) > 3 and partes[3].strip() else None
    subgrupo = partes[4].strip() if len(partes) > 4 and partes[4].strip() else None

    if grupo and ":" in grupo:
        return None
    if subgrupo and ":" in subgrupo:
        return None

    campos = _extrair_campos(partes[5:] if len(partes) > 5 else [])

    cartao = campos.get("cartao") or campos.get("cartão")
    data_pagamento = _parse_data_pagamento(campos.get("pagamento"), data_gasto) or data_gasto

    parcelas = _parse_parcelas(campos.get("parcelas"))
    if parcelas is None:
        return None

    inicio_parcela = None
    if parcelas > 1:
        inicio_parcela = _parse_inicio_parcela(campos.get("inicio"))
        if inicio_parcela is None:
            return None

    return LancamentoDTO(
        data_gasto=data_gasto,
        descricao=descricao,
        valor=valor,
        grupo=grupo or "",
        subgrupo=subgrupo or "",
        cartao=cartao,
        data_pagamento=data_pagamento,
        texto_original=texto.strip(),
        parcelas=parcelas,
        inicio_parcela=inicio_parcela,
    )


def parse_lancamento_multiplo(texto: str) -> tuple[date, list[str]] | None:
    """
    Detecta e extrai formato múltiplo: primeira linha é data isolada, resto são lançamentos.
    Retorna (data_cabeçalho, lista_de_linhas_de_lançamento) ou None se não é formato múltiplo.
    """
    linhas = texto.strip().split("\n")
    if len(linhas) < 2:
        return None

    primeira_linha = linhas[0].strip()
    data_gasto = _parse_data_gasto(primeira_linha)
    if data_gasto is None:
        return None

    linhas_lancamento = [l.strip() for l in linhas[1:] if l.strip()]
    if not linhas_lancamento:
        return None

    return (data_gasto, linhas_lancamento)


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


def parse_resumo_periodo(texto: str) -> ResumoPeriodoDTO | None:
    match = _RESUMO_PERIODO_RE.match(texto.strip())
    if not match:
        return None

    data_inicio_str = match.group(1)
    data_fim_str = match.group(2)

    data_inicio = _parse_data_periodo(data_inicio_str)
    data_fim = _parse_data_periodo(data_fim_str)

    if data_inicio is None or data_fim is None:
        return None

    if data_inicio > data_fim:
        return None

    return ResumoPeriodoDTO(data_inicio=data_inicio, data_fim=data_fim)


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

    mes_str = match.group(4)
    mes = None
    if mes_str:
        mes = _parse_mes_ano(mes_str)
        if mes is None:
            return None

    return OrcamentoDTO(grupo=grupo, subgrupo=subgrupo, valor=valor, mes=mes)


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


def parse_alias(texto: str) -> AliasDTO | None:
    """
    Parseia comando de criação de alias.

    Formatos aceitos:
    - alias: padaria → Alimentação > Padaria
    - alias: padaria -> Alimentação > Padaria
    """
    match = _ALIAS_RE.match(texto.strip())
    if not match:
        return None

    palavra_chave = match.group(1).strip()
    grupo = match.group(2).strip()
    subgrupo = match.group(3).strip()

    if not palavra_chave or not grupo or not subgrupo:
        return None
    if ":" in grupo or ":" in subgrupo:
        return None

    return AliasDTO(palavra_chave=palavra_chave, grupo=grupo, subgrupo=subgrupo)


def parse_remove_alias(texto: str) -> RemoveAliasDTO | None:
    """Parseia comando de remoção de alias."""
    match = _REMOVE_ALIAS_RE.match(texto.strip())
    if not match:
        return None
    palavra_chave = match.group(1).strip()
    if not palavra_chave:
        return None
    return RemoveAliasDTO(palavra_chave=palavra_chave)


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


def _parse_data_periodo(texto: str) -> date | None:
    match = re.match(r"^(\d{2})/(\d{2})$", texto.strip())
    if not match:
        return None
    dia, mes = int(match.group(1)), int(match.group(2))
    ano = date.today().year
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


def detectar_erro_parcelas(texto: str) -> str | None:
    partes = [p.strip() for p in texto.strip().split(" - ")]
    if len(partes) < 5:
        return None
    campos = _extrair_campos(partes[5:])
    parcelas_str = campos.get("parcelas")
    if parcelas_str:
        try:
            parcelas = int(parcelas_str.strip())
            if parcelas < 1:
                return "❌ Campo 'parcelas' deve ser >= 1"
            if parcelas > 60:
                return "❌ Campo 'parcelas' não pode ser > 60 (máximo razoável)"
            if parcelas > 1 and not campos.get("inicio"):
                return "❌ Campo 'inicio: MM/AA' é obrigatório quando parcelas > 1"
        except (ValueError, TypeError):
            return "❌ Campo 'parcelas' deve ser um número inteiro"
    if campos.get("inicio"):
        if not campos.get("parcelas"):
            return None
        try:
            mes, ano = int(campos.get("inicio").split("/")[0]), int(campos.get("inicio").split("/")[1])
            if mes < 1 or mes > 12:
                return f"❌ Mês inválido em 'inicio: {campos.get('inicio')}' (deve ser 01-12)"
        except (ValueError, IndexError):
            return f"❌ Formato inválido em 'inicio: {campos.get('inicio')}' (use MM/AA)"
    return None


def _parse_parcelas(texto: str | None) -> int | None:
    if not texto:
        return 1
    try:
        parcelas = int(texto.strip())
        if parcelas < 1:
            return None
        if parcelas > 60:
            return None
        return parcelas
    except (ValueError, TypeError):
        return None


def _parse_inicio_parcela(texto: str | None) -> date | None:
    if not texto:
        return None
    match = re.match(r"^(\d{2})/(\d{2})$", texto.strip())
    if not match:
        return None
    mes, ano = int(match.group(1)), int(match.group(2))
    if mes < 1 or mes > 12:
        return None
    ano = 2000 + ano if ano < 100 else ano
    try:
        return date(ano, mes, 1)
    except ValueError:
        return None


def _parse_mes_ano(texto: str) -> date | None:
    match = re.match(r"^(\d{2})/(\d{2})$", texto.strip())
    if not match:
        return None
    mes, ano = int(match.group(1)), int(match.group(2))
    if mes < 1 or mes > 12:
        return None
    ano = 2000 + ano if ano < 100 else ano
    try:
        return date(ano, mes, 1)
    except ValueError:
        return None


def parse_lembrete(texto: str) -> LembreteDTO | None:
    """
    Parseia comando de criação de lembrete.
    Formatos aceitos:
    - lembrete: aluguel - dia 5
    - lembrete: aluguel - dia 5 - auto
    """
    match = _LEMBRETE_RE.match(texto.strip())
    if not match:
        return None

    template_nome = match.group(1).strip()
    dia_vencimento = int(match.group(2))
    auto = match.group(3) is not None and match.group(3).lower() == "auto"

    if not template_nome or not (1 <= dia_vencimento <= 31):
        return None

    return LembreteDTO(template_nome=template_nome, dia_vencimento=dia_vencimento, auto=auto)


def parse_remove_lembrete(texto: str) -> RemoveLembreteDTO | None:
    """Parseia comando de remoção de lembrete."""
    match = _REMOVE_LEMBRETE_RE.match(texto.strip())
    if not match:
        return None
    template_nome = match.group(1).strip()
    if not template_nome:
        return None
    return RemoveLembreteDTO(template_nome=template_nome)


def parse_lancar_template(texto: str) -> LancarTemplateDTO | None:
    """Parseia comando de lançamento manual de template."""
    match = _LANCAR_TEMPLATE_RE.match(texto.strip())
    if not match:
        return None
    template_nome = match.group(1).strip()
    if not template_nome:
        return None
    return LancarTemplateDTO(template_nome=template_nome)
