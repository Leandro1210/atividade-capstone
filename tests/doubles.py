"""Test doubles reutilizáveis.

* **Stub** (:class:`StubRegistryService`): só fornece dados de *entrada* fixos e
  controlados. Os testes nunca fazem asserções sobre ele.
* **Mock** (:func:`make_antifraud_mock`): registra as interações de *saída* para que
  o teste verifique chamadas, contagem e parâmetros enviados.
* **Fake** (:class:`FakeClock`): implementação simplificada e controlável do relógio.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import create_autospec

from src.services.gateways import HttpAntiFraudGateway, RegistryResult, RegistryStatus


class StubRegistryService:
    """Retorna situação cadastral pré-definida por documento."""

    def __init__(
        self,
        statuses: dict[str, RegistryStatus] | None = None,
        default: RegistryStatus = RegistryStatus.REGULAR,
    ) -> None:
        self._statuses = statuses or {}
        self._default = default

    def lookup(self, document: str) -> RegistryResult:
        return RegistryResult(document, self._statuses.get(document, self._default))


def make_antifraud_mock():
    """Mock com a mesma assinatura do gateway real (autospec impede chamadas inválidas)."""
    return create_autospec(HttpAntiFraudGateway, instance=True, spec_set=True)


class FakeClock:
    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 1, 10, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def set(self, value: datetime) -> None:
        self.now = value

    def advance(self, **kwargs: float) -> None:
        self.now += timedelta(**kwargs)
