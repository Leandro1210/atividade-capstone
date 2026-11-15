"""Casos de uso da carteira digital."""

import hashlib
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal

from src.domain.document import normalize_document
from src.domain.exceptions import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InvalidPeriodError,
    RegistryRejectedError,
)
from src.domain.models import Account, Transaction, TransactionType, Transfer
from src.domain.money import from_cents, to_cents
from src.domain.transfer_rules import plan_transfer
from src.repositories.account_repository import AccountRepository
from src.repositories.database import Database
from src.repositories.idempotency_repository import IdempotencyRepository
from src.repositories.transaction_repository import TransactionRepository
from src.services.gateways import AntiFraudGateway, RegistryService, RegistryStatus

logger = logging.getLogger(__name__)

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class TransferOutcome:
    transfer: Transfer
    replayed: bool


@dataclass(frozen=True)
class Statement:
    account: Account
    transactions: list[Transaction]


class WalletService:
    def __init__(
        self,
        database: Database,
        antifraud_gateway: AntiFraudGateway,
        registry_service: RegistryService,
        *,
        clock: Clock = utc_now,
        max_transfer_cents: int | None = None,
        accounts: AccountRepository | None = None,
        transactions: TransactionRepository | None = None,
        idempotency: IdempotencyRepository | None = None,
    ) -> None:
        self._db = database
        self._antifraud = antifraud_gateway
        self._registry = registry_service
        self._clock = clock
        self._max_transfer_cents = max_transfer_cents
        self._accounts = accounts or AccountRepository()
        self._transactions = transactions or TransactionRepository()
        self._idempotency = idempotency or IdempotencyRepository()

    def close(self) -> None:
        self._db.close()

    # ------------------------------------------------------------------ contas
    def create_account(self, owner_name: str, document: str, initial_balance: Decimal) -> Account:
        normalized = normalize_document(document)
        initial_cents = to_cents(initial_balance, allow_zero=True)

        registry = self._registry.lookup(normalized)
        if registry.status is not RegistryStatus.REGULAR:
            raise RegistryRejectedError(f"Documento com situação cadastral {registry.status.value}")

        now = self._clock()
        account = Account(
            id=str(uuid.uuid4()),
            owner_name=owner_name.strip(),
            document=normalized,
            balance_cents=initial_cents,
            created_at=now,
        )
        with self._db.transaction() as conn:
            self._accounts.add(conn, account)
            if initial_cents > 0:
                self._transactions.add(
                    conn,
                    Transaction(
                        id=str(uuid.uuid4()),
                        account_id=account.id,
                        type=TransactionType.CREDIT,
                        amount_cents=initial_cents,
                        description="Saldo inicial",
                        created_at=now,
                    ),
                )
        return account

    def get_account(self, account_id: str) -> Account:
        with self._db.read() as conn:
            return self._require_account(conn, account_id)

    # ---------------------------------------------------------- transferências
    def transfer(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: Decimal,
        description: str = "",
        idempotency_key: str | None = None,
    ) -> TransferOutcome:
        amount_cents = to_cents(amount)
        request_hash = _hash_request(source_account_id, destination_account_id, amount_cents)

        with self._db.transaction() as conn:
            if idempotency_key:
                record = self._idempotency.get(conn, idempotency_key)
                if record is not None:
                    if record.request_hash != request_hash:
                        raise IdempotencyConflictError(
                            "Idempotency-Key já utilizada com outro payload"
                        )
                    transfer = self._transactions.get_transfer(conn, record.transfer_id)
                    return TransferOutcome(transfer=transfer, replayed=True)

            source = self._require_account(conn, source_account_id)
            destination = self._require_account(conn, destination_account_id)
            plan = plan_transfer(
                source_account_id=source.id,
                destination_account_id=destination.id,
                source_balance_cents=source.balance_cents,
                destination_balance_cents=destination.balance_cents,
                amount_cents=amount_cents,
                max_transfer_cents=self._max_transfer_cents,
            )

            now = self._clock()
            transfer = Transfer(
                id=str(uuid.uuid4()),
                source_account_id=source.id,
                destination_account_id=destination.id,
                amount_cents=plan.amount_cents,
                description=description or "Transferência",
                created_at=now,
            )
            self._accounts.update_balance(conn, source.id, plan.source_balance_after)
            self._accounts.update_balance(conn, destination.id, plan.destination_balance_after)
            self._transactions.add_transfer(conn, transfer)
            self._record_entries(conn, transfer)
            if idempotency_key:
                self._idempotency.save(conn, idempotency_key, request_hash, transfer.id, now)

        self._notify_antifraud(transfer)
        return TransferOutcome(transfer=transfer, replayed=False)

    # ------------------------------------------------------------------ extrato
    def statement(
        self,
        account_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        type_: TransactionType | None = None,
    ) -> Statement:
        if start_date and end_date and start_date > end_date:
            raise InvalidPeriodError("start_date não pode ser posterior a end_date")

        start = datetime.combine(start_date, time.min, UTC) if start_date else None
        end_exclusive = datetime.combine(end_date, time.min, UTC) if end_date else None

        with self._db.read() as conn:
            account = self._require_account(conn, account_id)
            entries = self._transactions.list_by_account(
                conn, account_id, start=start, end_exclusive=end_exclusive, type_=type_
            )
        return Statement(account=account, transactions=entries)

    # ---------------------------------------------------------------- internos
    def _require_account(self, conn, account_id: str) -> Account:
        account = self._accounts.get(conn, account_id)
        if account is None:
            raise AccountNotFoundError(f"Conta {account_id} não encontrada")
        return account

    def _record_entries(self, conn, transfer: Transfer) -> None:
        for account_id, counterparty, type_ in (
            (transfer.source_account_id, transfer.destination_account_id, TransactionType.DEBIT),
            (transfer.destination_account_id, transfer.source_account_id, TransactionType.CREDIT),
        ):
            self._transactions.add(
                conn,
                Transaction(
                    id=str(uuid.uuid4()),
                    account_id=account_id,
                    type=type_,
                    amount_cents=transfer.amount_cents,
                    description=transfer.description,
                    transfer_id=transfer.id,
                    counterparty_account_id=counterparty,
                    created_at=transfer.created_at,
                ),
            )

    def _notify_antifraud(self, transfer: Transfer) -> None:
        payload = {
            "event": "transfer.completed",
            "transfer_id": transfer.id,
            "source_account_id": transfer.source_account_id,
            "destination_account_id": transfer.destination_account_id,
            "amount": str(from_cents(transfer.amount_cents)),
            "currency": "BRL",
            "occurred_at": transfer.created_at.isoformat(),
        }
        try:
            self._antifraud.notify_transfer(payload)
        except Exception:
            # A transferência já foi efetivada: falha no gateway não pode desfazê-la.
            logger.exception("Falha ao notificar anti-fraude para transfer %s", transfer.id)


def _hash_request(source_id: str, destination_id: str, amount_cents: int) -> str:
    body = json.dumps([source_id, destination_id, amount_cents]).encode()
    return hashlib.sha256(body).hexdigest()
