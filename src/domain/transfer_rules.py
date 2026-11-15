"""Regras puras de cálculo de transferências financeiras."""

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
    raise NotImplementedError
