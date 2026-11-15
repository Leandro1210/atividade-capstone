import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    request_hash: str
    transfer_id: str


class IdempotencyRepository:
    def get(self, conn: sqlite3.Connection, key: str) -> IdempotencyRecord | None:
        row = conn.execute(
            "SELECT key, request_hash, transfer_id FROM idempotency_keys WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        return IdempotencyRecord(row["key"], row["request_hash"], row["transfer_id"])

    def save(
        self,
        conn: sqlite3.Connection,
        key: str,
        request_hash: str,
        transfer_id: str,
        created_at: datetime,
    ) -> None:
        conn.execute(
            "INSERT INTO idempotency_keys (key, request_hash, transfer_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            (key, request_hash, transfer_id, created_at.isoformat(timespec="microseconds")),
        )
