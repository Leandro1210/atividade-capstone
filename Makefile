PYTHON ?= python
HOST ?= http://127.0.0.1:8000
USERS ?= 50
DURATION ?= 60s

.PHONY: install lint format test-unit test-integration test-e2e test coverage coverage-gate run load clean

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test-unit:
	$(PYTHON) -m pytest tests/unit -m unit

test-integration:
	$(PYTHON) -m pytest tests/integration -m integration

test-e2e:
	$(PYTHON) -m pytest tests/e2e -m e2e

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html --cov-report=json --junitxml=reports/junit.xml

coverage-gate: coverage
	$(PYTHON) scripts/check_coverage.py reports/coverage.json --lines 85 --branches 80

run:
	$(PYTHON) -m uvicorn src.main:app --reload

load:
	mkdir -p reports/load
	locust -f tests/load/locustfile.py --headless -u $(USERS) -r $(USERS) -t $(DURATION) \
		--host $(HOST) --csv reports/load/wallet --only-summary
	$(PYTHON) scripts/load_report.py reports/load/wallet_stats.csv --max-error-rate 1.0

clean:
	rm -rf reports .pytest_cache .ruff_cache .coverage
