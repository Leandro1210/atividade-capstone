from decimal import Decimal

import pytest

from src.repositories.database import Database
from src.services.wallet_service import WalletService
from tests.doubles import FakeClock, StubRegistryService, make_antifraud_mock

# CPFs válidos (dígitos verificadores corretos) usados nos testes.
CPF_ALICE = "52998224725"
CPF_BRUNO = "11144477735"
CPF_CARLA = "39053344705"


@pytest.fixture
def database():
    db = Database(":memory:")
    yield db
    db.close()


@pytest.fixture
def antifraud_mock():
    return make_antifraud_mock()


@pytest.fixture
def registry_stub():
    return StubRegistryService()


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def service(database, antifraud_mock, registry_stub, clock):
    return WalletService(
        database,
        antifraud_mock,
        registry_stub,
        clock=clock,
        max_transfer_cents=1_000_000,  # R$ 10.000,00
    )


@pytest.fixture
def alice(service):
    return service.create_account("Alice", CPF_ALICE, Decimal("1000.00"))


@pytest.fixture
def bruno(service):
    return service.create_account("Bruno", CPF_BRUNO, Decimal("50.00"))


def pytest_collection_modifyitems(items):
    """Aplica o marcador da camada (unit/integration/e2e) conforme a pasta do teste."""
    for item in items:
        for layer in ("unit", "integration", "e2e"):
            if f"tests/{layer}/" in item.path.as_posix():
                item.add_marker(getattr(pytest.mark, layer))
