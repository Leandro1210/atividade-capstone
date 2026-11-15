from decimal import Decimal

from src.config import Settings
from src.main import build_wallet_service
from src.services.gateways import HttpAntiFraudGateway, LoggingAntiFraudGateway


def test_usa_valores_padrao_sem_variaveis_de_ambiente(monkeypatch):
    for var in ("DATABASE_URL", "ANTIFRAUD_WEBHOOK_URL", "MAX_TRANSFER_AMOUNT", "LOG_LEVEL"):
        monkeypatch.delenv(var, raising=False)

    settings = Settings.from_env()

    assert settings.database_url == ":memory:"
    assert settings.antifraud_webhook_url == ""
    assert settings.max_transfer_amount == Decimal("100000.00")


def test_le_configuracao_das_variaveis_de_ambiente(monkeypatch):
    monkeypatch.setenv("ANTIFRAUD_WEBHOOK_URL", "https://antifraude.example/webhook")
    monkeypatch.setenv("ANTIFRAUD_TIMEOUT_SECONDS", "0.5")
    monkeypatch.setenv("MAX_TRANSFER_AMOUNT", "250.00")

    settings = Settings.from_env()

    assert settings.antifraud_webhook_url == "https://antifraude.example/webhook"
    assert settings.antifraud_timeout_seconds == 0.5
    assert settings.max_transfer_amount == Decimal("250.00")


def test_usa_gateway_http_quando_webhook_configurado():
    service = build_wallet_service(Settings(antifraud_webhook_url="https://x.example/hook"))
    service.close()

    assert isinstance(service._antifraud, HttpAntiFraudGateway)


def test_usa_gateway_de_log_quando_webhook_ausente():
    service = build_wallet_service(Settings())
    service.close()

    assert isinstance(service._antifraud, LoggingAntiFraudGateway)
