from datetime import date
from decimal import Decimal

import pytest

from app.services.parser import parse_alias, parse_lancamento, parse_orcamento, parse_remove_alias, parse_resumo_periodo


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

    def test_lancamento_parcelado_valido(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 12 - inicio: 06/26"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_gasto == date(2026, 5, 1)
        assert dto.descricao == "tv samsung"
        assert dto.valor == Decimal("1200")
        assert dto.grupo == "Casa"
        assert dto.subgrupo == "Eletrodoméstico"
        assert dto.parcelas == 12
        assert dto.inicio_parcela == date(2026, 6, 1)

    def test_lancamento_parcelado_sem_inicio_retorna_none(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 12"
        assert parse_lancamento(texto) is None

    def test_lancamento_parcelado_inicio_invalido_retorna_none(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 12 - inicio: 13/26"
        assert parse_lancamento(texto) is None

    def test_parcelas_zero_retorna_none(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 0 - inicio: 06/26"
        assert parse_lancamento(texto) is None

    def test_parcelas_negativo_retorna_none(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: -5 - inicio: 06/26"
        assert parse_lancamento(texto) is None

    def test_parcelas_maior_60_retorna_none(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 61 - inicio: 06/26"
        assert parse_lancamento(texto) is None

    def test_lancamento_parcela_1_sem_inicio(self):
        texto = "01/05/26 - tv samsung - 1200 - Casa - Eletrodoméstico - parcelas: 1"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.parcelas == 1
        assert dto.inicio_parcela is None

    def test_lancamento_sem_parcelas_default_1(self):
        texto = "25/05/26 - padaria - 25 - Alimentação - Padaria"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.parcelas == 1
        assert dto.inicio_parcela is None


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


class TestParseResumoPeriodo:
    def test_periodo_valido(self):
        dto = parse_resumo_periodo("resumo: 01/05 a 15/05")

        assert dto is not None
        assert dto.data_inicio == date(2026, 5, 1)
        assert dto.data_fim == date(2026, 5, 15)

    def test_periodo_outro(self):
        dto = parse_resumo_periodo("resumo: 10/05 a 25/05")

        assert dto is not None
        assert dto.data_inicio == date(2026, 5, 10)
        assert dto.data_fim == date(2026, 5, 25)

    def test_periodo_mesmo_dia(self):
        dto = parse_resumo_periodo("resumo: 10/05 a 10/05")

        assert dto is not None
        assert dto.data_inicio == date(2026, 5, 10)
        assert dto.data_fim == date(2026, 5, 10)

    def test_periodo_invertido_retorna_none(self):
        dto = parse_resumo_periodo("resumo: 15/05 a 01/05")
        assert dto is None

    def test_periodo_sem_a_retorna_none(self):
        assert parse_resumo_periodo("resumo: 01/05 15/05") is None

    def test_periodo_com_espaco_errado_retorna_none(self):
        assert parse_resumo_periodo("resumo: 01/05a15/05") is None

    def test_data_invalida_retorna_none(self):
        assert parse_resumo_periodo("resumo: 99/99 a 15/05") is None

    def test_comando_vazio_retorna_none(self):
        assert parse_resumo_periodo("resumo:") is None

    def test_resumo_sem_periodo_retorna_none(self):
        assert parse_resumo_periodo("resumo") is None

    def test_resumo_grupo_nao_e_periodo(self):
        assert parse_resumo_periodo("resumo: Alimentação") is None

    def test_resumo_mes_ano_nao_e_periodo(self):
        assert parse_resumo_periodo("resumo: 05/26") is None


class TestParseAlias:
    def test_alias_com_seta_unicode(self):
        texto = "alias: padaria → Alimentação > Padaria"
        dto = parse_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "padaria"
        assert dto.grupo == "Alimentação"
        assert dto.subgrupo == "Padaria"

    def test_alias_com_seta_ascii(self):
        texto = "alias: uber -> Transporte > App"
        dto = parse_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "uber"
        assert dto.grupo == "Transporte"
        assert dto.subgrupo == "App"

    def test_alias_case_insensitive(self):
        texto = "ALIAS: netflix → LAZER > STREAMING"
        dto = parse_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "netflix"
        assert dto.grupo == "LAZER"
        assert dto.subgrupo == "STREAMING"

    def test_alias_com_espacos(self):
        texto = "alias: padaria   →   Alimentação   >   Padaria"
        dto = parse_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "padaria"
        assert dto.grupo == "Alimentação"
        assert dto.subgrupo == "Padaria"

    def test_alias_palavra_chave_vazia_retorna_none(self):
        assert parse_alias("alias:  → Alimentação > Padaria") is None

    def test_alias_grupo_vazio_retorna_none(self):
        assert parse_alias("alias: padaria →  > Padaria") is None

    def test_alias_subgrupo_vazio_retorna_none(self):
        assert parse_alias("alias: padaria → Alimentação > ") is None

    def test_alias_sem_seta_retorna_none(self):
        assert parse_alias("alias: padaria Alimentação > Padaria") is None

    def test_alias_com_dois_pontos_grupo_retorna_none(self):
        assert parse_alias("alias: padaria → grupo: Alimentação > Padaria") is None

    def test_alias_formato_invalido_retorna_none(self):
        assert parse_alias("oi tudo bem") is None

    def test_remove_alias_valido(self):
        texto = "remove alias: padaria"
        dto = parse_remove_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "padaria"

    def test_remove_alias_case_insensitive(self):
        texto = "REMOVE ALIAS: NETFLIX"
        dto = parse_remove_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "NETFLIX"

    def test_remove_alias_com_espacos(self):
        texto = "remove alias:  padaria  "
        dto = parse_remove_alias(texto)

        assert dto is not None
        assert dto.palavra_chave == "padaria"

    def test_remove_alias_vazio_retorna_none(self):
        assert parse_remove_alias("remove alias: ") is None

    def test_remove_alias_sem_dois_pontos_retorna_none(self):
        assert parse_remove_alias("remove alias padaria") is None

    def test_lancamento_curto_sem_grupo_subgrupo(self):
        texto = "25/05/26 - padaria - 25"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_gasto == date(2026, 5, 25)
        assert dto.descricao == "padaria"
        assert dto.valor == Decimal("25")
        assert dto.grupo == ""
        assert dto.subgrupo == ""

    def test_lancamento_curto_com_campos_opcionais(self):
        texto = "25/05/26 - padaria - 25 - cartao: bradesco"
        dto = parse_lancamento(texto)

        assert dto is not None
        assert dto.data_gasto == date(2026, 5, 25)
        assert dto.descricao == "padaria"
        assert dto.valor == Decimal("25")
        assert dto.grupo == ""
        assert dto.subgrupo == ""
        assert dto.cartao == "bradesco"
