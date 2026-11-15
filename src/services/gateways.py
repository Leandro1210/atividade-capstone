"""Portas (interfaces) e adaptadores para serviços externos.

* :class:`AntiFraudGateway` — saída: notifica o gateway anti-fraude fictício via
  webhook. Nos testes é substituído por **Mocks** (verificação de interações).
* :class:`RegistryService` — entrada: consulta de situação cadastral do CPF.
  Nos testes é substituído por **Stubs** (dados fixos e controlados).
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

import httpx

from src.domain.document import is_valid_cpf

logger = logging.getLogger(__name__)


class AntiFraudGateway(Protocol):
    def notify_transfer(self, payload: dict[str, Any]) -> None: ...


class RegistryStatus(StrEnum):
    REGULAR = "REGULAR"
    IRREGULAR = "IRREGULAR"
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True)
class RegistryResult:
    document: str
    status: RegistryStatus


class RegistryService(Protocol):
    def lookup(self, document: str) -> RegistryResult: ...


class HttpAntiFraudGateway:
    """Envia o evento de transferência como POST JSON para a URL do webhook."""

    def __init__(self, webhook_url: str, timeout_seconds: float = 2.0) -> None:
        self._webhook_url = webhook_url
        self._timeout = timeout_seconds

    def notify_transfer(self, payload: dict[str, Any]) -> None:
        response = httpx.post(self._webhook_url, json=payload, timeout=self._timeout)
        response.raise_for_status()


class LoggingAntiFraudGateway:
    """Adaptador usado quando nenhum webhook está configurado (ambiente local)."""

    def notify_transfer(self, payload: dict[str, Any]) -> None:
        logger.info("antifraud.notify %s", payload)


class LocalRegistryService:
    """Validação cadastral local: CPF com dígitos verificadores válidos é REGULAR."""

    def lookup(self, document: str) -> RegistryResult:
        status = RegistryStatus.REGULAR if is_valid_cpf(document) else RegistryStatus.NOT_FOUND
        return RegistryResult(document=document, status=status)
