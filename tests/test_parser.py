from datetime import date
from decimal import Decimal

import pytest

from app.services.parser import parse_lancamento, parse_orcamento


class TestParseLancamento:
    def test_mensagem_completa(self):
        texto = "25/05/26 - padaria - 25 - Alimentação - Padaria - cartao: bradesco - pagamento: 20/06"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_gasto == date(2026, 5, 25)
        assert dto.descricao == "padaria"
        assert dto.valor == Decimal("25")
        assert dto.grupo == "Alimentação"
        assert dto.subgrupo == "Padaria"
        assert dto.cartao == "bradesco"
        assert dto.data_pagamento == date(2026, 6, 20)
        assert dto.texto_original == texto

    def test_mensagem_minima(self):
        texto = "25/05/26 - uber - 18 - Transporte - App"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_gasto == date(2026, 5, 25)
        assert dto.descricao == "uber"
        assert dto.valor == Decimal("18")
        assert dto.grupo == "Transporte"
        assert dto.subgrupo == "App"
        assert dto.cartao is None
        assert dto.data_pagamento == date(2026, 5, 25)  # defaults to data_gasto

    def test_sem_pagamento_usa_data_gasto(self):
        texto = "10/03/26 - mercado - 200 - Alimentação - Supermercado - cartao: nubank"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_pagamento == date(2026, 3, 10)

    def test_valor_com_centavos(self):
        texto = "01/01/26 - mercado - 149,90 - Alimentação - Supermercado"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.valor == Decimal("149.90")

    def test_pagamento_ano_seguinte(self):
        texto = "15/12/26 - restaurante - 80 - Alimentação - Restaurante - pagamento: 10/01"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_pagamento == date(2027, 1, 10)

    def test_sem_subgrupo_retorna_none(self):
        texto = "25/05/26 - uber - 18 - Transporte"
        assert parse_lancamento(texto) is None

    def test_sem_grupo_retorna_none(self):
        texto = "25/05/26 - padaria - 25"
        assert parse_lancamento(texto) is None

    def test_data_invalida_retorna_none(self):
        assert parse_lancamento("99/99/26 - padaria - 25 - Alimentação - Padaria") is None

    def test_valor_zero_retorna_none(self):
        assert parse_lancamento("25/05/26 - padaria - 0 - Alimentação - Padaria") is None

    def test_mensagem_aleatoria_retorna_none(self):
        assert parse_lancamento("oi, tudo bem?") is None

    def test_mensagem_vazia_retorna_none(self):
        assert parse_lancamento("") is None

    def test_comando_orcamento_nao_e_lancamento(self):
        assert parse_lancamento("orçamento: alimentação - 500") is None

    def test_grupo_com_dois_pontos_retorna_none(self):
        # rejeita formato antigo onde grupo vinha como "grupo: X"
        assert parse_lancamento("25/05/26 - mercado - 50 - grupo: Alimentação - Supermercado") is None


class TestParseOrcamento:
    def test_orcamento_valido(self):
        dto = parse_orcamento("orçamento: ref. fora de casa - 300")

        assert dto is not None
        assert dto.grupo == "ref. fora de casa"
        assert dto.valor == Decimal("300")

    def test_orcamento_sem_acento(self):
        dto = parse_orcamento("orcamento: transporte - 150")

        assert dto is not None
        assert dto.grupo == "transporte"
        assert dto.valor == Decimal("150")

    def test_orcamento_com_centavos(self):
        dto = parse_orcamento("orçamento: alimentação - 1500,00")

        assert dto is not None
        assert dto.valor == Decimal("1500.00")

    def test_orcamento_invalido_retorna_none(self):
        assert parse_orcamento("25/05/26 - padaria - 25 - Alimentação - Padaria") is None

    def test_lancamento_nao_e_orcamento(self):
        assert parse_orcamento("oi tudo bem") is None
