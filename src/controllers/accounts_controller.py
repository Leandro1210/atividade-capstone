from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.controllers.dependencies import get_wallet_service
from src.controllers.schemas import (
    AccountResponse,
    CreateAccountRequest,
    StatementResponse,
    TransactionResponse,
)
from src.domain.models import TransactionType
from src.domain.money import from_cents
from src.services.wallet_service import WalletService

router = APIRouter(prefix="/accounts", tags=["accounts"])

Service = Annotated[WalletService, Depends(get_wallet_service)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AccountResponse)
def create_account(body: CreateAccountRequest, service: Service) -> AccountResponse:
    account = service.create_account(body.owner_name, body.document, body.initial_balance)
    return AccountResponse.from_domain(account)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, service: Service) -> AccountResponse:
    return AccountResponse.from_domain(service.get_account(account_id))


@router.get("/{account_id}/statement", response_model=StatementResponse)
def get_statement(
    account_id: str,
    service: Service,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    type: Annotated[TransactionType | None, Query()] = None,
) -> StatementResponse:
    statement = service.statement(account_id, start_date, end_date, type)
    credits = sum(
        t.amount_cents for t in statement.transactions if t.type is TransactionType.CREDIT
    )
    debits = sum(t.amount_cents for t in statement.transactions if t.type is TransactionType.DEBIT)
    return StatementResponse(
        account_id=statement.account.id,
        owner_name=statement.account.owner_name,
        balance=from_cents(statement.account.balance_cents),
        total_credits=from_cents(credits),
        total_debits=from_cents(debits),
        transactions=[TransactionResponse.from_domain(t) for t in statement.transactions],
    )
