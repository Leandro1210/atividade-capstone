"""Transferências com persistência real (SQLite em memória) e idempotência."""

from decimal import Decimal

import pytest

from src.domain.exceptions import (
    AccountNotFoundError,
    IdempotencyConflictError,
    InsufficientFundsError,
    TransferLimitExceededError,
)
from src.domain.models import TransactionType


def test_transferencia_atualiza_saldos_das_duas_contas(service, alice, bruno):
    outcome = service.transfer(alice.id, bruno.id, Decimal("200.00"), "Aluguel")

    assert outcome.replayed is False
    assert outcome.transfer.amount_cents == 20_000
    assert outcome.transfer.description == "Aluguel"
    assert service.get_account(alice.id).balance_cents == 80_000
    assert service.get_account(bruno.id).balance_cents == 25_000


def test_transferencia_gera_lancamentos_de_debito_e_credito(service, alice, bruno):
    transfer = service.transfer(alice.id, bruno.id, Decimal("10.00")).transfer

    debit = service.statement(alice.id, type_=TransactionType.DEBIT).transactions
    credit = service.statement(bruno.id, type_=TransactionType.CREDIT).transactions[-1]

    assert [(d.transfer_id, d.amount_cents, d.counterparty_account_id) for d in debit] == [
        (transfer.id, 1_000, bruno.id)
    ]
    assert (credit.transfer_id, credit.counterparty_account_id) == (transfer.id, alice.id)
    assert transfer.description == "Transferência"


def test_saldo_insuficiente_nao_altera_saldos_nem_lancamentos(service, alice, bruno):
    with pytest.raises(InsufficientFundsError):
        service.transfer(bruno.id, alice.id, Decimal("50.01"))

    assert service.get_account(bruno.id).balance_cents == 5_000
    assert service.get_account(alice.id).balance_cents == 100_000
    assert len(service.statement(bruno.id).transactions) == 1  # só o saldo inicial


def test_respeita_limite_por_transferencia(service, alice, bruno):
    with pytest.raises(TransferLimitExceededError):
        service.transfer(alice.id, bruno.id, Decimal("10000.01"))


@pytest.mark.parametrize("missing", ["source", "destination"])
def test_conta_inexistente(service, alice, missing):
    source, destination = (
        ("nao-existe", alice.id) if missing == "source" else (alice.id, "nao-existe")
    )
    with pytest.raises(AccountNotFoundError):
        service.transfer(source, destination, Decimal("1"))


def test_idempotencia_repete_resposta_sem_debitar_novamente(service, alice, bruno):
    first = service.transfer(alice.id, bruno.id, Decimal("30"), idempotency_key="key-1")
    second = service.transfer(alice.id, bruno.id, Decimal("30"), idempotency_key="key-1")

    assert first.replayed is False
    assert second.replayed is True
    assert second.transfer == first.transfer
    assert service.get_account(alice.id).balance_cents == 97_000


def test_idempotencia_com_payload_diferente_e_conflito(service, alice, bruno):
    service.transfer(alice.id, bruno.id, Decimal("30"), idempotency_key="key-1")

    with pytest.raises(IdempotencyConflictError):
        service.transfer(alice.id, bruno.id, Decimal("31"), idempotency_key="key-1")

    assert service.get_account(alice.id).balance_cents == 97_000


def test_chaves_diferentes_geram_transferencias_diferentes(service, alice, bruno):
    a = service.transfer(alice.id, bruno.id, Decimal("1"), idempotency_key="k-a")
    b = service.transfer(alice.id, bruno.id, Decimal("1"), idempotency_key="k-b")

    assert a.transfer.id != b.transfer.id
    assert service.get_account(alice.id).balance_cents == 99_800


def test_transferencia_que_falha_nao_consome_a_chave_de_idempotencia(service, alice, bruno):
    with pytest.raises(InsufficientFundsError):
        service.transfer(bruno.id, alice.id, Decimal("999"), idempotency_key="k-1")

    retry = service.transfer(bruno.id, alice.id, Decimal("5"), idempotency_key="k-1")
    assert retry.replayed is False
