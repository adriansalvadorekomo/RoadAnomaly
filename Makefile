# RoadAnomaly — developer workflow
#
# Run `make help` for the target list. Anything not yet implemented is
# written down here on purpose: status lives in docs/validation/requirements-matrix.md.

.DEFAULT_GOAL := help
PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help venv install lint fmt type test test-fast data-check data-audit \
        data-audit-check architecture train eval export serve landing prototype up down clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Create the local virtual environment
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install: venv ## Install dev + deep learning + API + prototype dependencies
	$(BIN)/pip install -r requirements/dl.txt -r requirements/api-base.txt -r requirements/prototype.txt -r requirements/dev.txt

lint: ## Ruff lint + format check
	$(BIN)/ruff check .
	$(BIN)/ruff format --check .

fmt: ## Auto-format and auto-fix
	$(BIN)/ruff format .
	$(BIN)/ruff check --fix .

type: ## Static type check
	$(BIN)/mypy dl backend tests

test: ## Full test suite
	$(BIN)/pytest

test-fast: ## Tests that need no GPU and no training
	$(BIN)/pytest -m "not slow"

data-check: ## Validate the RoadAnomaly checkout (frame <-> label contract)
	$(BIN)/pytest tests/dataset -v

data-audit: ## Generate the schema-validated dataset audit evidence
	PYTHONDONTWRITEBYTECODE=1 $(BIN)/python -m dl.data.audit

data-audit-check: ## Validate the committed dataset audit pair without writing
	PYTHONDONTWRITEBYTECODE=1 $(BIN)/python -m dl.data.audit --check

architecture: ## Render the C4 diagrams (Java + Chromium) and refresh the manifest
	./docs/architecture/render.sh

train: ## Train one model. Usage: make train CONFIG=configs/autoencoder.yaml
	$(BIN)/python -m dl.training.train --config $(CONFIG)

eval: ## Evaluate a checkpoint. Usage: make eval CKPT=artifacts/best.keras
	$(BIN)/python -m dl.evaluation.evaluate --ckpt $(CKPT)

export: ## Export a checkpoint to a SavedModel for the API
	$(BIN)/python -m dl.inference.export_savedmodel --ckpt $(CKPT)

serve: ## Run the FastAPI inference service on :8000
	cd backend && ../$(BIN)/uvicorn app.main:app --reload --port 8000

landing: ## Run the Astro landing page on :4321
	cd frontend/landing && npm run dev

prototype: ## Run the Streamlit prototype on :8501
	$(BIN)/streamlit run frontend/prototype/app.py --server.port 8501

up: ## Bring up the local stack (API + prototype) with compose
	docker compose -f infra/compose/docker-compose.yml up --build

down: ## Stop the stack
	docker compose -f infra/compose/docker-compose.yml down

clean: ## Remove caches and local artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
