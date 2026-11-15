"""Uso de **Mock** para verificar as interações de saída com o gateway anti-fraude.

As asserções aqui são sobre o *comportamento* (quantas vezes e com quais
parâmetros o colaborador externo foi chamado), não sobre valores de retorno.
"""

from decimal import Decimal

import pytest

from src.domain.exceptions import InsufficientFundsError, SameAccountTransferError


def test_notifica_antifraude_uma_vez_com_payload_completo(service, antifraud_mock, alice, bruno):
    transfer = service.transfer(alice.id, bruno.id, Decimal("123.45")).transfer

    antifraud_mock.notify_transfer.assert_called_once_with(
        {
            "event": "transfer.completed",
            "transfer_id": transfer.id,
            "source_account_id": alice.id,
            "destination_account_id": bruno.id,
            "amount": "123.45",
            "currency": "BRL",
            "occurred_at": "2026-01-10T12:00:00+00:00",
        }
    )


def test_conta_uma_notificacao_por_transferencia(service, antifraud_mock, alice, bruno):
    for _ in range(3):
        service.transfer(alice.id, bruno.id, Decimal("1"))

    assert antifraud_mock.notify_transfer.call_count == 3
    transfer_ids = {c.args[0]["transfer_id"] for c in antifraud_mock.notify_transfer.call_args_list}
    assert len(transfer_ids) == 3


@pytest.mark.parametrize(
    ("origem", "destino", "valor", "erro"),
    [
        ("bruno", "alice", "999", InsufficientFundsError),
        ("alice", "alice", "1", SameAccountTransferError),
    ],
)
def test_nao_notifica_quando_transferencia_falha(
    service, antifraud_mock, alice, bruno, origem, destino, valor, erro
):
    accounts = {"alice": alice.id, "bruno": bruno.id}

    with pytest.raises(erro):
        service.transfer(accounts[origem], accounts[destino], Decimal(valor))

    antifraud_mock.notify_transfer.assert_not_called()


def test_nao_notifica_novamente_em_replay_idempotente(service, antifraud_mock, alice, bruno):
    service.transfer(alice.id, bruno.id, Decimal("5"), idempotency_key="abc")
    service.transfer(alice.id, bruno.id, Decimal("5"), idempotency_key="abc")

    antifraud_mock.notify_transfer.assert_called_once()


def test_criacao_de_conta_nao_notifica_antifraude(service, antifraud_mock):
    service.create_account("Carla", "39053344705", Decimal("10"))

    antifraud_mock.notify_transfer.assert_not_called()
