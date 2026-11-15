"""Contrato de erros HTTP da API."""

import pytest

CPF_ALICE = "52998224725"
CPF_BRUNO = "11144477735"


@pytest.fixture
def accounts(client):
    alice = client.post(
        "/accounts", json={"owner_name": "Alice", "document": CPF_ALICE, "initial_balance": "100"}
    ).json()
    bruno = client.post(
        "/accounts", json={"owner_name": "Bruno", "document": CPF_BRUNO, "initial_balance": "0"}
    ).json()
    return alice, bruno


def _transfer(client, source, destination, amount, key=None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        "/transfers",
        json={"source_account_id": source, "destination_account_id": destination, "amount": amount},
        headers=headers,
    )


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_conta_inexistente_retorna_404(client):
    response = client.get("/accounts/nao-existe")

    assert response.status_code == 404
    assert response.json()["code"] == "account_not_found"


def test_documento_duplicado_retorna_409(client, accounts):
    response = client.post("/accounts", json={"owner_name": "X", "document": CPF_ALICE})

    assert response.status_code == 409
    assert response.json()["code"] == "duplicate_document"


def test_cpf_invalido_retorna_422(client):
    response = client.post("/accounts", json={"owner_name": "X", "document": "12345678900"})

    assert response.status_code == 422
    assert response.json()["code"] == "registry_rejected"


@pytest.mark.parametrize(
    "body",
    [
        {"owner_name": "", "document": CPF_ALICE},
        {"owner_name": "X", "document": CPF_ALICE, "initial_balance": "-1"},
        {"document": CPF_ALICE},
    ],
)
def test_payload_invalido_de_conta_retorna_422(client, body):
    assert client.post("/accounts", json=body).status_code == 422


def test_saldo_insuficiente_retorna_422(client, accounts):
    alice, bruno = accounts

    response = _transfer(client, bruno["id"], alice["id"], "0.01")

    assert response.status_code == 422
    assert response.json() == {
        "code": "insufficient_funds",
        "message": "Saldo insuficiente para a transferência",
    }


def test_mesma_conta_retorna_422(client, accounts):
    alice, _ = accounts

    response = _transfer(client, alice["id"], alice["id"], "1")

    assert response.json()["code"] == "same_account_transfer"


def test_limite_excedido_retorna_422(client, accounts):
    alice, bruno = accounts

    response = _transfer(client, alice["id"], bruno["id"], "5000.01")

    assert response.json()["code"] == "transfer_limit_exceeded"


@pytest.mark.parametrize("amount", ["0", "-10", "1.234", "abc"])
def test_valor_invalido_retorna_422(client, accounts, amount):
    alice, bruno = accounts

    assert _transfer(client, alice["id"], bruno["id"], amount).status_code == 422


def test_transferencia_para_conta_inexistente_retorna_404(client, accounts):
    alice, _ = accounts

    assert _transfer(client, alice["id"], "nao-existe", "1").status_code == 404


def test_reuso_de_chave_com_payload_diferente_retorna_409(client, accounts):
    alice, bruno = accounts
    _transfer(client, alice["id"], bruno["id"], "1", key="k")

    response = _transfer(client, alice["id"], bruno["id"], "2", key="k")

    assert response.status_code == 409
    assert response.json()["code"] == "idempotency_conflict"


def test_periodo_invertido_no_extrato_retorna_422(client, accounts):
    alice, _ = accounts

    response = client.get(
        f"/accounts/{alice['id']}/statement",
        params={"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )

    assert response.json()["code"] == "invalid_period"


def test_tipo_invalido_no_extrato_retorna_422(client, accounts):
    alice, _ = accounts

    response = client.get(f"/accounts/{alice['id']}/statement", params={"type": "pix"})

    assert response.status_code == 422
