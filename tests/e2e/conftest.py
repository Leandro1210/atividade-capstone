import socket
import threading
import time
from decimal import Decimal

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient

from src.config import Settings
from src.main import create_app


@pytest.fixture
def client():
    """Aplicação completa (rotas, validação, handlers, serviço e SQLite reais)."""
    app = create_app(Settings(database_url=":memory:", max_transfer_amount=Decimal("5000.00")))
    with TestClient(app) as test_client:
        yield test_client


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def live_server():
    """Sobe o Uvicorn em uma porta real para testes via socket HTTP."""
    port = _free_port()
    config = uvicorn.Config(
        create_app(Settings()), host="127.0.0.1", port=port, log_level="warning"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            if httpx.get(f"{base_url}/health").status_code == 200:
                break
        except httpx.TransportError:
            time.sleep(0.05)
    else:  # pragma: no cover - só acontece se o servidor não subir
        pytest.fail("Servidor não iniciou a tempo")

    yield base_url
    server.should_exit = True
    thread.join(timeout=10)
