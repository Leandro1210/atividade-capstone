"""Regras puras de cálculo de transferências financeiras.

Este módulo não conhece banco de dados, HTTP ou relógio: recebe valores e
devolve um :class:`TransferPlan` ou levanta uma exceção de domínio. Por isso é
o alvo principal dos testes unitários escritos em TDD.
"""

from src.domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    SameAccountTransferError,
    TransferLimitExceededError,
)
from src.domain.models import TransferPlan


def plan_transfer(
    *,
    source_account_id: str,
    destination_account_id: str,
    source_balance_cents: int,
    destination_balance_cents: int,
    amount_cents: int,
    max_transfer_cents: int | None = None,
) -> TransferPlan:
    """Valida a transferência e calcula os saldos resultantes."""
    _ensure_distinct_accounts(source_account_id, destination_account_id)
    _ensure_positive_amount(amount_cents)
    _ensure_within_limit(amount_cents, max_transfer_cents)
    _ensure_sufficient_funds(source_balance_cents, amount_cents)

    return TransferPlan(
        source_balance_after=source_balance_cents - amount_cents,
        destination_balance_after=destination_balance_cents + amount_cents,
        amount_cents=amount_cents,
    )


def _ensure_distinct_accounts(source_id: str, destination_id: str) -> None:
    if source_id == destination_id:
        raise SameAccountTransferError("Conta de origem e destino devem ser diferentes")


def _ensure_positive_amount(amount_cents: int) -> None:
    if amount_cents <= 0:
        raise InvalidAmountError("Valor da transferência deve ser positivo")


def _ensure_within_limit(amount_cents: int, max_transfer_cents: int | None) -> None:
    if max_transfer_cents is not None and amount_cents > max_transfer_cents:
        raise TransferLimitExceededError("Valor excede o limite por transferência")


def _ensure_sufficient_funds(balance_cents: int, amount_cents: int) -> None:
    if amount_cents > balance_cents:
        raise InsufficientFundsError("Saldo insuficiente para a transferência")
