"""Entidades do domínio."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TransactionType(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


@dataclass(frozen=True)
class Account:
    id: str
    owner_name: str
    document: str
    balance_cents: int
    created_at: datetime


@dataclass(frozen=True)
class Transaction:
    id: str
    account_id: str
    type: TransactionType
    amount_cents: int
    description: str
    created_at: datetime
    transfer_id: str | None = None
    counterparty_account_id: str | None = None


@dataclass(frozen=True)
class Transfer:
    id: str
    source_account_id: str
    destination_account_id: str
    amount_cents: int
    description: str
    created_at: datetime


@dataclass(frozen=True)
class TransferPlan:
    """Resultado puro do cálculo de uma transferência (sem efeitos colaterais)."""

    source_balance_after: int
    destination_balance_after: int
    amount_cents: int
