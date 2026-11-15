from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from src.controllers.dependencies import get_wallet_service
from src.controllers.schemas import TransferRequest, TransferResponse
from src.services.wallet_service import WalletService

router = APIRouter(prefix="/transfers", tags=["transfers"])

Service = Annotated[WalletService, Depends(get_wallet_service)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransferResponse)
def create_transfer(
    body: TransferRequest,
    response: Response,
    service: Service,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=128)] = None,
) -> TransferResponse:
    outcome = service.transfer(
        source_account_id=body.source_account_id,
        destination_account_id=body.destination_account_id,
        amount=body.amount,
        description=body.description,
        idempotency_key=idempotency_key,
    )
    if outcome.replayed:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotent-Replayed"] = "true"
    return TransferResponse.from_domain(outcome.transfer)
