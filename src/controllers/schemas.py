"""Contratos HTTP (DTOs) da API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.domain.models import Account, Transaction, TransactionType, Transfer
from src.domain.money import from_cents


class CreateAccountRequest(BaseModel):
    owner_name: str = Field(min_length=1, max_length=120)
    document: str = Field(min_length=11, max_length=14, description="CPF com ou sem máscara")
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)


class AccountResponse(BaseModel):
    id: str
    owner_name: str
    document: str
    balance: Decimal
    created_at: datetime

    @classmethod
    def from_domain(cls, account: Account) -> "AccountResponse":
        return cls(
            id=account.id,
            owner_name=account.owner_name,
            document=account.document,
            balance=from_cents(account.balance_cents),
            created_at=account.created_at,
        )


class TransferRequest(BaseModel):
    source_account_id: str = Field(min_length=1)
    destination_account_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    description: str = Field(default="", max_length=140)


class TransferResponse(BaseModel):
    id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    description: str
    created_at: datetime

    @classmethod
    def from_domain(cls, transfer: Transfer) -> "TransferResponse":
        return cls(
            id=transfer.id,
            source_account_id=transfer.source_account_id,
            destination_account_id=transfer.destination_account_id,
            amount=from_cents(transfer.amount_cents),
            description=transfer.description,
            created_at=transfer.created_at,
        )


class TransactionResponse(BaseModel):
    id: str
    type: TransactionType
    amount: Decimal
    description: str
    transfer_id: str | None
    counterparty_account_id: str | None
    created_at: datetime

    @classmethod
    def from_domain(cls, tx: Transaction) -> "TransactionResponse":
        return cls(
            id=tx.id,
            type=tx.type,
            amount=from_cents(tx.amount_cents),
            description=tx.description,
            transfer_id=tx.transfer_id,
            counterparty_account_id=tx.counterparty_account_id,
            created_at=tx.created_at,
        )


class StatementResponse(BaseModel):
    account_id: str
    owner_name: str
    balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    transactions: list[TransactionResponse]


class ErrorResponse(BaseModel):
    code: str
    message: str
