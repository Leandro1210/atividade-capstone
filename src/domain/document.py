"""Regras puras de documento (CPF)."""

import re

_NON_DIGITS = re.compile(r"\D")


def normalize_document(document: str) -> str:
    """Remove pontuação do CPF, mantendo apenas dígitos."""
    return _NON_DIGITS.sub("", document or "")


def is_valid_cpf(document: str) -> bool:
    """Valida os dígitos verificadores de um CPF."""
    digits = normalize_document(document)
    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    numbers = [int(d) for d in digits]
    for position in (9, 10):
        total = sum(numbers[i] * (position + 1 - i) for i in range(position))
        check_digit = (total * 10) % 11 % 10
        if numbers[position] != check_digit:
            return False
    return True
