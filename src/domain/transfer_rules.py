"""Regras puras de cálculo de transferências financeiras."""

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
    if source_account_id == destination_account_id:
        raise SameAccountTransferError("Conta de origem e destino devem ser diferentes")
    if amount_cents <= 0:
        raise InvalidAmountError("Valor da transferência deve ser positivo")
    if max_transfer_cents is not None and amount_cents > max_transfer_cents:
        raise TransferLimitExceededError("Valor excede o limite por transferência")
    if amount_cents > source_balance_cents:
        raise InsufficientFundsError("Saldo insuficiente para a transferência")
    return TransferPlan(
        source_balance_after=source_balance_cents - amount_cents,
        destination_balance_after=destination_balance_cents + amount_cents,
        amount_cents=amount_cents,
    )
