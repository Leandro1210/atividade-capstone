"""Fluxo ponta a ponta: registro de contas → transferência → extrato final."""

from datetime import UTC, datetime, timedelta

import httpx

CPF_ALICE = "529.982.247-25"
CPF_BRUNO = "111.444.777-35"


def _create_account(http, name, document, balance):
    response = http.post(
        "/accounts", json={"owner_name": name, "document": document, "initial_balance": balance}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_fluxo_completo_registro_transferencia_e_extrato(client):
    alice = _create_account(client, "Alice", CPF_ALICE, "500.00")
    bruno = _create_account(client, "Bruno", CPF_BRUNO, "20.00")
    assert alice["balance"] == "500.00"
    assert alice["document"] == "52998224725"

    response = client.post(
        "/transfers",
        json={
            "source_account_id": alice["id"],
            "destination_account_id": bruno["id"],
            "amount": "120.50",
            "description": "Pagamento do freela",
        },
        headers={"Idempotency-Key": "pedido-001"},
    )
    assert response.status_code == 201, response.text
    transfer = response.json()
    assert transfer["amount"] == "120.50"
    assert "Idempotent-Replayed" not in response.headers

    assert client.get(f"/accounts/{alice['id']}").json()["balance"] == "379.50"
    assert client.get(f"/accounts/{bruno['id']}").json()["balance"] == "140.50"

    statement = client.get(f"/accounts/{alice['id']}/statement").json()
    assert statement["balance"] == "379.50"
    assert statement["total_credits"] == "500.00"
    assert statement["total_debits"] == "120.50"
    assert [(t["type"], t["amount"]) for t in statement["transactions"]] == [
        ("credit", "500.00"),
        ("debit", "120.50"),
    ]
    last = statement["transactions"][-1]
    assert last["transfer_id"] == transfer["id"]
    assert last["counterparty_account_id"] == bruno["id"]
    assert last["description"] == "Pagamento do freela"


def test_extrato_filtrado_por_tipo_e_data(client):
    alice = _create_account(client, "Alice", CPF_ALICE, "100.00")
    bruno = _create_account(client, "Bruno", CPF_BRUNO, "100.00")
    for amount in ("10.00", "15.00"):
        client.post(
            "/transfers",
            json={
                "source_account_id": alice["id"],
                "destination_account_id": bruno["id"],
                "amount": amount,
            },
        )
    today = datetime.now(UTC).date()

    debits = client.get(
        f"/accounts/{alice['id']}/statement",
        params={"type": "debit", "start_date": str(today - timedelta(days=1))},
    ).json()
    future = client.get(
        f"/accounts/{alice['id']}/statement",
        params={"start_date": str(today + timedelta(days=1))},
    ).json()

    assert [t["amount"] for t in debits["transactions"]] == ["10.00", "15.00"]
    assert debits["total_debits"] == "25.00"
    assert debits["total_credits"] == "0.00"
    assert future["transactions"] == []


def test_replay_idempotente_via_http(client):
    alice = _create_account(client, "Alice", CPF_ALICE, "100.00")
    bruno = _create_account(client, "Bruno", CPF_BRUNO, "0")
    body = {
        "source_account_id": alice["id"],
        "destination_account_id": bruno["id"],
        "amount": "40.00",
    }

    first = client.post("/transfers", json=body, headers={"Idempotency-Key": "k-1"})
    second = client.post("/transfers", json=body, headers={"Idempotency-Key": "k-1"})

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.headers["Idempotent-Replayed"] == "true"
    assert second.json() == first.json()
    assert client.get(f"/accounts/{alice['id']}").json()["balance"] == "60.00"


def test_fluxo_em_servidor_real_via_socket(live_server):
    with httpx.Client(base_url=live_server) as http:
        alice = _create_account(http, "Alice", CPF_ALICE, "10.00")
        bruno = _create_account(http, "Bruno", CPF_BRUNO, "0")

        response = http.post(
            "/transfers",
            json={
                "source_account_id": alice["id"],
                "destination_account_id": bruno["id"],
                "amount": "10.00",
            },
        )
        statement = http.get(f"/accounts/{bruno['id']}/statement").json()

    assert response.status_code == 201
    assert statement["balance"] == "10.00"
    assert statement["transactions"][0]["type"] == "credit"
