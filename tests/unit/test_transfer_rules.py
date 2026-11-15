"""Regras puras de transferência — escritas em TDD (Red → Green → Refactor)."""

import pytest

from src.domain.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    SameAccountTransferError,
    TransferLimitExceededError,
)
from src.domain.transfer_rules import plan_transfer


def _plan(**overrides):
    params = {
        "source_account_id": "A",
        "destination_account_id": "B",
        "source_balance_cents": 10_000,
        "destination_balance_cents": 500,
        "amount_cents": 2_500,
        "max_transfer_cents": None,
    }
    params.update(overrides)
    return plan_transfer(**params)


def test_debita_origem_e_credita_destino():
    plan = _plan()

    assert plan.source_balance_after == 7_500
    assert plan.destination_balance_after == 3_000
    assert plan.amount_cents == 2_500


def test_conserva_o_total_de_dinheiro_entre_as_contas():
    plan = _plan(source_balance_cents=12_345, destination_balance_cents=678, amount_cents=999)

    assert plan.source_balance_after + plan.destination_balance_after == 12_345 + 678


def test_permite_transferir_exatamente_todo_o_saldo():
    plan = _plan(source_balance_cents=2_500, amount_cents=2_500)

    assert plan.source_balance_after == 0


def test_rejeita_saldo_insuficiente_por_um_centavo():
    with pytest.raises(InsufficientFundsError, match="Saldo insuficiente"):
        _plan(source_balance_cents=2_499, amount_cents=2_500)


@pytest.mark.parametrize("amount", [0, -1, -10_000])
def test_rejeita_valor_nao_positivo(amount):
    with pytest.raises(InvalidAmountError):
        _plan(amount_cents=amount)


def test_rejeita_transferencia_para_a_mesma_conta():
    with pytest.raises(SameAccountTransferError):
        _plan(source_account_id="A", destination_account_id="A")


def test_rejeita_valor_acima_do_limite():
    with pytest.raises(TransferLimitExceededError):
        _plan(amount_cents=5_001, max_transfer_cents=5_000)


def test_aceita_valor_igual_ao_limite():
    plan = _plan(amount_cents=5_000, max_transfer_cents=5_000)

    assert plan.source_balance_after == 5_000


def test_mesma_conta_tem_precedencia_sobre_saldo_insuficiente():
    with pytest.raises(SameAccountTransferError):
        _plan(source_account_id="A", destination_account_id="A", source_balance_cents=0)
