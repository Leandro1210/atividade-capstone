"""Regressão do hotfix: ``end_date`` deve incluir o dia inteiro informado."""

from datetime import UTC, date, datetime
from decimal import Decimal


def test_end_date_inclui_lancamentos_do_proprio_dia(service, clock, alice, bruno):
    clock.set(datetime(2026, 3, 20, 23, 59, 59, tzinfo=UTC))
    service.transfer(alice.id, bruno.id, Decimal("1"))

    statement = service.statement(
        alice.id, start_date=date(2026, 3, 20), end_date=date(2026, 3, 20)
    )

    assert [t.amount_cents for t in statement.transactions] == [100]


def test_end_date_exclui_lancamentos_do_dia_seguinte(service, clock, alice, bruno):
    clock.set(datetime(2026, 3, 21, 0, 0, tzinfo=UTC))
    service.transfer(alice.id, bruno.id, Decimal("1"))

    statement = service.statement(
        alice.id, start_date=date(2026, 3, 20), end_date=date(2026, 3, 20)
    )

    assert statement.transactions == []
