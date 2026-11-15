"""Casos de uso da carteira digital."""

from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal

from src.repositories.database import Database
from src.services.gateways import AntiFraudGateway, RegistryService

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class WalletService:
    def __init__(
        self,
        database: Database,
        antifraud_gateway: AntiFraudGateway,
        registry_service: RegistryService,
        *,
        clock: Clock = utc_now,
        max_transfer_cents: int | None = None,
    ) -> None:
        self._db = database

    def close(self) -> None:
        self._db.close()

    def create_account(self, owner_name: str, document: str, initial_balance: Decimal):
        raise NotImplementedError

    def get_account(self, account_id: str):
        raise NotImplementedError

    def transfer(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: Decimal,
        description: str = "",
        idempotency_key: str | None = None,
    ):
        raise NotImplementedError

    def statement(
        self,
        account_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        type_=None,
    ):
        raise NotImplementedError
