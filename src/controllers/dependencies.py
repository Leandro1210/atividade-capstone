from fastapi import Request

from src.services.wallet_service import WalletService


def get_wallet_service(request: Request) -> WalletService:
    return request.app.state.wallet_service
