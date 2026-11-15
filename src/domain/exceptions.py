"""Exceções de domínio da Wallet API.

Cada exceção carrega um ``code`` estável, usado pela camada HTTP para montar
respostas de erro previsíveis para os clientes da API.
"""


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidAmountError(DomainError):
    code = "invalid_amount"


class InsufficientFundsError(DomainError):
    code = "insufficient_funds"


class SameAccountTransferError(DomainError):
    code = "same_account_transfer"


class TransferLimitExceededError(DomainError):
    code = "transfer_limit_exceeded"


class AccountNotFoundError(DomainError):
    code = "account_not_found"


class DuplicateDocumentError(DomainError):
    code = "duplicate_document"


class RegistryRejectedError(DomainError):
    code = "registry_rejected"


class IdempotencyConflictError(DomainError):
    code = "idempotency_conflict"


class InvalidPeriodError(DomainError):
    code = "invalid_period"
