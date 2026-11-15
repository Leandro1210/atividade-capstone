"""Transferências concorrentes: sem saldo negativo, sem perda de dinheiro, sem deadlock."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from decimal import Decimal

from src.domain.exceptions import InsufficientFundsError

WORKERS = 50


def test_transferencias_concorrentes_nao_geram_saldo_negativo(service, alice, bruno):
    # Bruno tem R$ 50,00: só 25 das 50 transferências de R$ 2,00 podem passar.
    def transfer(_):
        try:
            service.transfer(bruno.id, alice.id, Decimal("2.00"))
            return "ok"
        except InsufficientFundsError:
            return "insufficient"

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(transfer, range(WORKERS), timeout=30))

    assert results.count("ok") == 25
    assert results.count("insufficient") == 25
    assert service.get_account(bruno.id).balance_cents == 0
    assert service.get_account(alice.id).balance_cents == 105_000


def test_transferencias_cruzadas_concorrentes_conservam_o_total(service, alice, bruno):
    def transfer(i):
        source, destination = (alice, bruno) if i % 2 == 0 else (bruno, alice)
        # Saldo insuficiente é aceitável: o importante é não criar nem destruir dinheiro.
        with suppress(InsufficientFundsError):
            service.transfer(source.id, destination.id, Decimal("1.00"))

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(transfer, range(WORKERS * 4), timeout=30))

    total = (
        service.get_account(alice.id).balance_cents + service.get_account(bruno.id).balance_cents
    )
    assert total == 105_000


def test_mesma_chave_de_idempotencia_em_paralelo_gera_uma_unica_transferencia(
    service, antifraud_mock, alice, bruno
):
    def transfer(_):
        return service.transfer(alice.id, bruno.id, Decimal("10"), idempotency_key="same-key")

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        outcomes = list(pool.map(transfer, range(WORKERS), timeout=30))

    assert len({o.transfer.id for o in outcomes}) == 1
    assert sum(not o.replayed for o in outcomes) == 1
    assert service.get_account(alice.id).balance_cents == 99_000
    antifraud_mock.notify_transfer.assert_called_once()
