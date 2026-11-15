import pytest

from src.domain.document import is_valid_cpf, normalize_document


def test_normaliza_removendo_pontuacao():
    assert normalize_document("529.982.247-25") == "52998224725"


def test_normaliza_documento_vazio():
    assert normalize_document("") == ""


@pytest.mark.parametrize("cpf", ["52998224725", "529.982.247-25", "11144477735"])
def test_aceita_cpf_valido(cpf):
    assert is_valid_cpf(cpf) is True


@pytest.mark.parametrize(
    ("cpf", "motivo"),
    [
        ("52998224715", "primeiro dígito verificador errado"),
        ("52998224726", "segundo dígito verificador errado"),
        ("11111111111", "todos os dígitos iguais"),
        ("1234567890", "menos de 11 dígitos"),
        ("123456789012", "mais de 11 dígitos"),
    ],
)
def test_rejeita_cpf_invalido(cpf, motivo):
    assert is_valid_cpf(cpf) is False, motivo
