from decimal import Decimal

import pytest

from src.domain.exceptions import InvalidAmountError
from src.domain.money import from_cents, to_cents


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("10.50"), 1050),
        (Decimal("0.01"), 1),
        ("99.9", 9990),
        (7, 700),
        (Decimal("1E+2"), 10_000),
    ],
)
def test_converte_valores_validos_para_centavos(value, expected):
    assert to_cents(value) == expected


def test_nao_sofre_erro_de_ponto_flutuante():
    assert to_cents("0.1") + to_cents("0.2") == to_cents("0.3")


@pytest.mark.parametrize("value", ["10.001", Decimal("0.005")])
def test_rejeita_mais_de_duas_casas_decimais(value):
    with pytest.raises(InvalidAmountError, match="2 casas decimais"):
        to_cents(value)


@pytest.mark.parametrize("value", [Decimal("-0.01"), "-5", 0])
def test_rejeita_valores_nao_positivos_por_padrao(value):
    with pytest.raises(InvalidAmountError, match="positivo"):
        to_cents(value)


def test_aceita_zero_quando_permitido():
    assert to_cents(Decimal("0"), allow_zero=True) == 0


def test_rejeita_negativo_mesmo_quando_zero_e_permitido():
    with pytest.raises(InvalidAmountError):
        to_cents(Decimal("-1"), allow_zero=True)


@pytest.mark.parametrize("value", ["abc", "", "1,50"])
def test_rejeita_texto_que_nao_e_numero(value):
    with pytest.raises(InvalidAmountError, match="inválido"):
        to_cents(value)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_rejeita_valores_nao_finitos(value):
    with pytest.raises(InvalidAmountError, match="finito"):
        to_cents(value)


@pytest.mark.parametrize(("cents", "expected"), [(1050, "10.50"), (1, "0.01"), (0, "0.00")])
def test_converte_centavos_para_decimal_com_duas_casas(cents, expected):
    assert from_cents(cents) == Decimal(expected)
    assert str(from_cents(cents)) == expected
