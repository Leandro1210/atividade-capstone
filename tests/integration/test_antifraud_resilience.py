"""Regressão do hotfix: falha no gateway anti-fraude não pode quebrar a transferência."""

from decimal import Decimal

import httpx


def test_transferencia_e_efetivada_mesmo_se_gateway_falhar(
    service, antifraud_mock, alice, bruno, caplog
):
    antifraud_mock.notify_transfer.side_effect = httpx.ConnectTimeout("gateway fora do ar")

    outcome = service.transfer(alice.id, bruno.id, Decimal("10"))

    antifraud_mock.notify_transfer.assert_called_once()
    assert service.get_account(alice.id).balance_cents == 99_000
    assert service.get_account(bruno.id).balance_cents == 6_000
    assert f"Falha ao notificar anti-fraude para transfer {outcome.transfer.id}" in caplog.text
