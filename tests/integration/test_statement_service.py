"""Extrato com filtros por data e tipo (relógio controlado por um Fake)."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.domain.exceptions import AccountNotFoundError, InvalidPeriodError
from src.domain.models import TransactionType


@pytest.fixture
def historico(service, clock, alice, bruno):
    """Alice criada em 10/01. Transferências em 11/01, 12/01 e 15/01."""
    clock.set(datetime(2026, 1, 11, 9, 0, tzinfo=UTC))
    service.transfer(alice.id, bruno.id, Decimal("10"))
    clock.set(datetime(2026, 1, 12, 18, 30, tzinfo=UTC))
    service.transfer(bruno.id, alice.id, Decimal("5"))
    clock.set(datetime(2026, 1, 15, 8, 0, tzinfo=UTC))
    service.transfer(alice.id, bruno.id, Decimal("20"))


def _amounts(statement):
    return [(t.type.value, t.amount_cents) for t in statement.transactions]


def test_extrato_sem_filtros_em_ordem_cronologica(service, alice, historico):
    statement = service.statement(alice.id)

    assert _amounts(statement) == [
        ("credit", 100_000),
        ("debit", 1_000),
        ("credit", 500),
        ("debit", 2_000),
    ]
    assert statement.account.balance_cents == 97_500


def test_filtra_por_tipo_debito(service, alice, historico):
    statement = service.statement(alice.id, type_=TransactionType.DEBIT)

    assert _amounts(statement) == [("debit", 1_000), ("debit", 2_000)]


def test_filtra_por_tipo_credito(service, alice, historico):
    statement = service.statement(alice.id, type_=TransactionType.CREDIT)

    assert _amounts(statement) == [("credit", 100_000), ("credit", 500)]


def test_filtra_por_data_inicial(service, alice, historico):
    statement = service.statement(alice.id, start_date=date(2026, 1, 12))

    assert _amounts(statement) == [("credit", 500), ("debit", 2_000)]


def test_filtra_por_periodo_e_tipo_combinados(service, alice, historico):
    statement = service.statement(
        alice.id,
        start_date=date(2026, 1, 11),
        end_date=date(2026, 1, 14),
        type_=TransactionType.DEBIT,
    )

    assert _amounts(statement) == [("debit", 1_000)]


def test_periodo_sem_movimentacao_retorna_lista_vazia(service, alice, historico):
    statement = service.statement(alice.id, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28))

    assert statement.transactions == []


def test_rejeita_periodo_invertido(service, alice):
    with pytest.raises(InvalidPeriodError):
        service.statement(alice.id, start_date=date(2026, 1, 5), end_date=date(2026, 1, 4))


def test_extrato_de_conta_inexistente(service):
    with pytest.raises(AccountNotFoundError):
        service.statement("nao-existe")
