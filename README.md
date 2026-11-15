# Wallet API — Microsserviço Financeiro com Self-Testing e CI

[![CI](https://github.com/Leandro1210/atividade-capstone/actions/workflows/ci.yml/badge.svg)](https://github.com/Leandro1210/atividade-capstone/actions/workflows/ci.yml)

API REST de carteira digital: contas, transferências idempotentes e concorrentes,
extrato com filtros e notificação anti-fraude via webhook.

A documentação formal (requisitos, arquitetura, estratégia de testes, CI e
métricas de carga) está em [RELATORIO_TECNICO.md](RELATORIO_TECNICO.md).

## Stack

Python 3.14 · FastAPI · SQLite (em memória) · PyTest + Coverage.py · Ruff · Locust · GitHub Actions

## Como executar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

uvicorn src.main:app --reload      # API em http://127.0.0.1:8000 (Swagger em /docs)
```

## Testes

```bash
pytest tests/unit                  # unitários (TDD)
pytest tests/integration           # integração (mocks, stubs, SQLite em memória)
pytest tests/e2e                   # ponta a ponta via HTTP

make coverage-gate                 # suíte completa + gate (linhas >= 85%, branches >= 80%)
make load                          # teste de carga (API precisa estar rodando)
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/accounts` | Cria conta com saldo inicial |
| `GET` | `/accounts/{id}` | Consulta conta e saldo |
| `GET` | `/accounts/{id}/statement?start_date=&end_date=&type=` | Extrato filtrado |
| `POST` | `/transfers` (header `Idempotency-Key`) | Transferência entre contas |
| `GET` | `/health` | Health check |
