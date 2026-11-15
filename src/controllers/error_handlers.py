from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AccountNotFoundError,
    DomainError,
    DuplicateDocumentError,
    IdempotencyConflictError,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    AccountNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateDocumentError: status.HTTP_409_CONFLICT,
    IdempotencyConflictError: status.HTTP_409_CONFLICT,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        http_status = STATUS_BY_ERROR.get(type(exc), status.HTTP_422_UNPROCESSABLE_CONTENT)
        return JSONResponse(
            status_code=http_status, content={"code": exc.code, "message": exc.message}
        )
