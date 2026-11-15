"""Configuração lida de variáveis de ambiente (ver ``.env.example``)."""

import os
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Settings:
    database_url: str = ":memory:"
    antifraud_webhook_url: str = ""
    antifraud_timeout_seconds: float = 2.0
    max_transfer_amount: Decimal = Decimal("100000.00")
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            antifraud_webhook_url=os.getenv("ANTIFRAUD_WEBHOOK_URL", cls.antifraud_webhook_url),
            antifraud_timeout_seconds=float(
                os.getenv("ANTIFRAUD_TIMEOUT_SECONDS", cls.antifraud_timeout_seconds)
            ),
            max_transfer_amount=Decimal(
                os.getenv("MAX_TRANSFER_AMOUNT", str(cls.max_transfer_amount))
            ),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
        )
