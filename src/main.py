"""Ponto de entrada da Wallet API.

Execução local: ``uvicorn src.main:app --reload``
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import Settings
from src.controllers import accounts_controller, transfers_controller
from src.controllers.error_handlers import register_error_handlers
from src.domain.money import to_cents
from src.repositories.database import Database
from src.services.gateways import (
    AntiFraudGateway,
    HttpAntiFraudGateway,
    LocalRegistryService,
    LoggingAntiFraudGateway,
    RegistryService,
)
from src.services.wallet_service import WalletService


def build_wallet_service(
    settings: Settings,
    *,
    antifraud_gateway: AntiFraudGateway | None = None,
    registry_service: RegistryService | None = None,
) -> WalletService:
    if antifraud_gateway is None:
        antifraud_gateway = (
            HttpAntiFraudGateway(settings.antifraud_webhook_url, settings.antifraud_timeout_seconds)
            if settings.antifraud_webhook_url
            else LoggingAntiFraudGateway()
        )
    return WalletService(
        Database(settings.database_url),
        antifraud_gateway,
        registry_service or LocalRegistryService(),
        max_transfer_cents=to_cents(settings.max_transfer_amount),
    )


def create_app(
    settings: Settings | None = None, *, wallet_service: WalletService | None = None
) -> FastAPI:
    settings = settings or Settings.from_env()
    logging.basicConfig(level=settings.log_level)

    service = wallet_service or build_wallet_service(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        service.close()

    app = FastAPI(title="Wallet API", version="1.0.0", lifespan=lifespan)
    app.state.wallet_service = service

    app.include_router(accounts_controller.router)
    app.include_router(transfers_controller.router)
    register_error_handlers(app)

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
