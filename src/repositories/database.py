"""Conexão SQLite compartilhada e controle transacional.

O banco padrão é ``:memory:``. Como o FastAPI executa endpoints síncronos em um
pool de threads, todo acesso à conexão é serializado por um ``RLock`` e as
escritas ocorrem dentro de ``BEGIN IMMEDIATE`` para garantir atomicidade.
"""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id            TEXT PRIMARY KEY,
    owner_name    TEXT NOT NULL,
    document      TEXT NOT NULL UNIQUE,
    balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0),
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transfers (
    id                     TEXT PRIMARY KEY,
    source_account_id      TEXT NOT NULL REFERENCES accounts(id),
    destination_account_id TEXT NOT NULL REFERENCES accounts(id),
    amount_cents           INTEGER NOT NULL CHECK (amount_cents > 0),
    description            TEXT NOT NULL,
    created_at             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id                      TEXT PRIMARY KEY,
    account_id              TEXT NOT NULL REFERENCES accounts(id),
    type                    TEXT NOT NULL CHECK (type IN ('debit', 'credit')),
    amount_cents            INTEGER NOT NULL CHECK (amount_cents > 0),
    description             TEXT NOT NULL,
    transfer_id             TEXT REFERENCES transfers(id),
    counterparty_account_id TEXT REFERENCES accounts(id),
    created_at              TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_date
    ON transactions (account_id, created_at);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key          TEXT PRIMARY KEY,
    request_hash TEXT NOT NULL,
    transfer_id  TEXT NOT NULL REFERENCES transfers(id),
    created_at   TEXT NOT NULL
);
"""


class Database:
    def __init__(self, url: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(url, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Executa um bloco atômico: commit em sucesso, rollback em erro."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            self._conn.execute("COMMIT")

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            yield self._conn

    def close(self) -> None:
        with self._lock:
            self._conn.close()
