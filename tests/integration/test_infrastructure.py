"""Adaptadores de infraestrutura: banco SQLite e cliente HTTP do webhook."""

from unittest.mock import Mock

import httpx
import pytest

from src.services import gateways
from src.services.gateways import (
    HttpAntiFraudGateway,
    LocalRegistryService,
    LoggingAntiFraudGateway,
    RegistryStatus,
)


def _insert_then_fail(database):
    with database.transaction() as conn:
        conn.execute(
            "INSERT INTO accounts VALUES ('x', 'X', '000', 100, '2026-01-01T00:00:00+00:00')"
        )
        raise RuntimeError("falha no meio da transação")


def test_transacao_faz_rollback_em_caso_de_erro(database):
    with pytest.raises(RuntimeError):
        _insert_then_fail(database)

    with database.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0


def test_banco_impede_saldo_negativo_via_constraint(database):
    with pytest.raises(Exception, match="CHECK constraint failed"), database.transaction() as conn:
        conn.execute(
            "INSERT INTO accounts VALUES ('x', 'X', '000', -1, '2026-01-01T00:00:00+00:00')"
        )


def test_gateway_http_envia_post_json_para_o_webhook(monkeypatch):
    response = httpx.Response(202, request=httpx.Request("POST", "https://af.example/hook"))
    post_mock = Mock(return_value=response)
    monkeypatch.setattr(gateways.httpx, "post", post_mock)

    HttpAntiFraudGateway("https://af.example/hook", timeout_seconds=1.5).notify_transfer({"a": 1})

    post_mock.assert_called_once_with("https://af.example/hook", json={"a": 1}, timeout=1.5)


def test_gateway_http_propaga_erro_de_status(monkeypatch):
    response = httpx.Response(500, request=httpx.Request("POST", "https://af.example/hook"))
    monkeypatch.setattr(gateways.httpx, "post", Mock(return_value=response))

    with pytest.raises(httpx.HTTPStatusError):
        HttpAntiFraudGateway("https://af.example/hook").notify_transfer({})


def test_gateway_de_log_registra_payload(caplog):
    caplog.set_level("INFO")

    LoggingAntiFraudGateway().notify_transfer({"transfer_id": "t-1"})

    assert "t-1" in caplog.text


@pytest.mark.parametrize(
    ("document", "status"),
    [("52998224725", RegistryStatus.REGULAR), ("12345678900", RegistryStatus.NOT_FOUND)],
)
def test_registro_local_valida_cpf(document, status):
    assert LocalRegistryService().lookup(document).status is status
