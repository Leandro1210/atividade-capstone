"""Conversão segura de valores monetários."""

from decimal import Decimal


def to_cents(value: Decimal | int | str, *, allow_zero: bool = False) -> int:
    raise NotImplementedError


def from_cents(cents: int) -> Decimal:
    raise NotImplementedError
