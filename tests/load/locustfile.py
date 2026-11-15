"""Teste de carga do endpoint de transferência.

Execução (API rodando em http://localhost:8000):

    locust -f tests/load/locustfile.py --headless -u 50 -r 50 -t 60s \
        --host http://localhost:8000 --csv reports/load/wallet

Cada usuário virtual cria duas contas próprias no ``on_start`` e então dispara
transferências entre elas (com ``Idempotency-Key`` única). Além disso, uma fração
das requisições é direcionada a um par de contas *compartilhado* por todos os
usuários, forçando disputa real pelo mesmo saldo (cenário de concorrência).
"""

import itertools
import random
import threading
import uuid

from locust import HttpUser, between, task

_cpf_lock = threading.Lock()
# Ponto de partida aleatório: permite repetir o teste contra o mesmo servidor sem colidir CPFs.
_cpf_counter = itertools.count(random.randrange(100_000_000, 900_000_000, 10_000))
_shared_accounts: list[str] = []
_shared_lock = threading.Lock()


def _generate_cpf() -> str:
    with _cpf_lock:
        base = [int(d) for d in str(next(_cpf_counter)).zfill(9)]
    for position in (9, 10):
        total = sum(base[i] * (position + 1 - i) for i in range(position))
        base.append((total * 10) % 11 % 10)
    return "".join(map(str, base))


def _create_account(client, name: str, balance: str) -> str:
    response = client.post(
        "/accounts",
        json={"owner_name": name, "document": _generate_cpf(), "initial_balance": balance},
        name="/accounts [setup]",
    )
    response.raise_for_status()
    return response.json()["id"]


def _ensure_shared_accounts(client) -> None:
    with _shared_lock:
        if not _shared_accounts:
            for name in ("Compartilhada A", "Compartilhada B"):
                _shared_accounts.append(_create_account(client, name, "1000000.00"))


class WalletUser(HttpUser):
    wait_time = between(0.05, 0.2)

    def on_start(self):
        _ensure_shared_accounts(self.client)
        self.accounts = [
            _create_account(self.client, f"Usuario {uuid.uuid4().hex[:6]}", "100000.00")
            for _ in range(2)
        ]

    def _transfer(self, source: str, destination: str, label: str):
        payload = {
            "source_account_id": source,
            "destination_account_id": destination,
            "amount": f"{random.randint(1, 500)}.{random.randint(0, 99):02d}",
        }
        with self.client.post(
            "/transfers",
            json=payload,
            headers={"Idempotency-Key": str(uuid.uuid4())},
            name=label,
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"status {response.status_code}: {response.text[:120]}")

    @task(3)
    def transfer_between_own_accounts(self):
        source, destination = random.sample(self.accounts, 2)
        self._transfer(source, destination, "/transfers [own]")

    @task(1)
    def transfer_on_shared_accounts(self):
        source, destination = random.sample(_shared_accounts, 2)
        self._transfer(source, destination, "/transfers [shared]")
