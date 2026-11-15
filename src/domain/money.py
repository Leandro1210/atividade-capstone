"""Conversão segura de valores monetários.

Todo valor é armazenado internamente em centavos (``int``) para evitar erros
de arredondamento de ponto flutuante.
"""

from decimal import Decimal, InvalidOperation

from src.domain.exceptions import InvalidAmountError

CENTS = Decimal("100")


def to_cents(value: Decimal | int | str, *, allow_zero: bool = False) -> int:
    """Converte um valor decimal em centavos, validando sinal e precisão."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InvalidAmountError(f"Valor monetário inválido: {value!r}") from exc

    if not amount.is_finite():
        raise InvalidAmountError("Valor monetário deve ser finito")
    if amount.as_tuple().exponent < -2:
        raise InvalidAmountError("Valor monetário aceita no máximo 2 casas decimais")
    if amount < 0 or (amount == 0 and not allow_zero):
        raise InvalidAmountError("Valor monetário deve ser positivo")

    return int(amount * CENTS)


def from_cents(cents: int) -> Decimal:
    """Converte centavos para ``Decimal`` com 2 casas decimais."""
    return (Decimal(cents) / CENTS).quantize(Decimal("0.01"))
