"""Criação/consulta de contas com SQLite em memória e Stub de validação cadastral."""

from decimal import Decimal

import pytest

from src.domain.exceptions import (
    AccountNotFoundError,
    DuplicateDocumentError,
    InvalidAmountError,
    RegistryRejectedError,
)
from src.domain.models import TransactionType
from src.services.gateways import RegistryStatus
from src.services.wallet_service import WalletService
from tests.conftest import CPF_ALICE, CPF_BRUNO
from tests.doubles import StubRegistryService


def test_cria_conta_e_persiste_no_banco(service, clock):
    account = service.create_account("  Alice  ", "529.982.247-25", Decimal("150.75"))

    stored = service.get_account(account.id)
    assert stored.owner_name == "Alice"
    assert stored.document == CPF_ALICE
    assert stored.balance_cents == 15_075
    assert stored.created_at == clock.now


def test_saldo_inicial_gera_lancamento_de_credito(service):
    account = service.create_account("Alice", CPF_ALICE, Decimal("100.00"))

    entries = service.statement(account.id).transactions
    assert len(entries) == 1
    assert entries[0].type is TransactionType.CREDIT
    assert entries[0].amount_cents == 10_000
    assert entries[0].description == "Saldo inicial"


def test_saldo_inicial_zero_nao_gera_lancamento(service):
    account = service.create_account("Alice", CPF_ALICE, Decimal("0"))

    assert service.statement(account.id).transactions == []
    assert service.get_account(account.id).balance_cents == 0


@pytest.mark.parametrize("status", [RegistryStatus.IRREGULAR, RegistryStatus.NOT_FOUND])
def test_rejeita_documento_com_situacao_cadastral_nao_regular(database, antifraud_mock, status):
    # Stub: fornece dado fixo de entrada para o CPF do Bruno.
    stub = StubRegistryService(statuses={CPF_BRUNO: status})
    service = WalletService(database, antifraud_mock, stub)

    with pytest.raises(RegistryRejectedError, match=status.value):
        service.create_account("Bruno", CPF_BRUNO, Decimal("10"))

    # Documento regular continua sendo aceito pelo mesmo stub.
    assert service.create_account("Alice", CPF_ALICE, Decimal("10")).document == CPF_ALICE


def test_documento_rejeitado_nao_persiste_conta(database, antifraud_mock):
    service = WalletService(
        database, antifraud_mock, StubRegistryService(default=RegistryStatus.IRREGULAR)
    )

    with pytest.raises(RegistryRejectedError):
        service.create_account("Bruno", CPF_BRUNO, Decimal("10"))

    with database.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0


def test_rejeita_documento_duplicado(service):
    service.create_account("Alice", CPF_ALICE, Decimal("10"))

    with pytest.raises(DuplicateDocumentError):
        service.create_account("Alice 2", "529.982.247-25", Decimal("10"))


def test_rejeita_saldo_inicial_com_tres_casas_decimais(service):
    with pytest.raises(InvalidAmountError):
        service.create_account("Alice", CPF_ALICE, Decimal("10.001"))


def test_consulta_de_conta_inexistente(service):
    with pytest.raises(AccountNotFoundError):
        service.get_account("nao-existe")
