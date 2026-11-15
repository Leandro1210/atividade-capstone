import sqlite3
from datetime import datetime

from src.domain.models import Transaction, TransactionType, Transfer


class TransactionRepository:
    def add_transfer(self, conn: sqlite3.Connection, transfer: Transfer) -> None:
        conn.execute(
            "INSERT INTO transfers (id, source_account_id, destination_account_id, "
            "amount_cents, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                transfer.id,
                transfer.source_account_id,
                transfer.destination_account_id,
                transfer.amount_cents,
                transfer.description,
                transfer.created_at.isoformat(timespec="microseconds"),
            ),
        )

    def get_transfer(self, conn: sqlite3.Connection, transfer_id: str) -> Transfer | None:
        row = conn.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,)).fetchone()
        if row is None:
            return None
        return Transfer(
            id=row["id"],
            source_account_id=row["source_account_id"],
            destination_account_id=row["destination_account_id"],
            amount_cents=row["amount_cents"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def add(self, conn: sqlite3.Connection, transaction: Transaction) -> None:
        conn.execute(
            "INSERT INTO transactions (id, account_id, type, amount_cents, description, "
            "transfer_id, counterparty_account_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                transaction.id,
                transaction.account_id,
                transaction.type.value,
                transaction.amount_cents,
                transaction.description,
                transaction.transfer_id,
                transaction.counterparty_account_id,
                transaction.created_at.isoformat(timespec="microseconds"),
            ),
        )

    def list_by_account(
        self,
        conn: sqlite3.Connection,
        account_id: str,
        *,
        start: datetime | None = None,
        end_exclusive: datetime | None = None,
        type_: TransactionType | None = None,
    ) -> list[Transaction]:
        """Lista lançamentos da conta em ordem cronológica.

        ``start`` é inclusivo e ``end_exclusive`` é exclusivo (intervalo semiaberto).
        """
        query = "SELECT * FROM transactions WHERE account_id = ?"
        params: list[object] = [account_id]
        if start is not None:
            query += " AND created_at >= ?"
            params.append(start.isoformat(timespec="microseconds"))
        if end_exclusive is not None:
            query += " AND created_at < ?"
            params.append(end_exclusive.isoformat(timespec="microseconds"))
        if type_ is not None:
            query += " AND type = ?"
            params.append(type_.value)
        query += " ORDER BY created_at, rowid"

        return [_to_transaction(row) for row in conn.execute(query, params).fetchall()]


def _to_transaction(row: sqlite3.Row) -> Transaction:
    return Transaction(
        id=row["id"],
        account_id=row["account_id"],
        type=TransactionType(row["type"]),
        amount_cents=row["amount_cents"],
        description=row["description"],
        transfer_id=row["transfer_id"],
        counterparty_account_id=row["counterparty_account_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
