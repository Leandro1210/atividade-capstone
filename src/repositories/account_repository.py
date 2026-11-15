import sqlite3
from datetime import datetime

from src.domain.exceptions import DuplicateDocumentError
from src.domain.models import Account


class AccountRepository:
    def add(self, conn: sqlite3.Connection, account: Account) -> None:
        try:
            conn.execute(
                "INSERT INTO accounts (id, owner_name, document, balance_cents, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    account.id,
                    account.owner_name,
                    account.document,
                    account.balance_cents,
                    account.created_at.isoformat(timespec="microseconds"),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateDocumentError("Já existe uma conta para este documento") from exc

    def get(self, conn: sqlite3.Connection, account_id: str) -> Account | None:
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        return _to_account(row) if row else None

    def update_balance(self, conn: sqlite3.Connection, account_id: str, balance_cents: int) -> None:
        conn.execute(
            "UPDATE accounts SET balance_cents = ? WHERE id = ?", (balance_cents, account_id)
        )


def _to_account(row: sqlite3.Row) -> Account:
    return Account(
        id=row["id"],
        owner_name=row["owner_name"],
        document=row["document"],
        balance_cents=row["balance_cents"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
