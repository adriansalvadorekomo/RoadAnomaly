# RoadAnomaly — developer workflow
#
# Run `make help` for the target list. Anything not yet implemented is
# written down here on purpose: the roadmap in README.md maps each target
# to the week it lands.

.DEFAULT_GOAL := help
PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: help venv install lint fmt type test test-fast data-check \
        train eval export serve ui up down clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

venv: ## Create the local virtual environment
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install: venv ## Install dev + deep learning + API dependencies
	$(BIN)/pip install -r requirements/dl.txt -r requirements/api.txt -r requirements/dev.txt

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
	$(BIN)/pytest tests/test_dataset_integrity.py -v

train: ## Train one model. Usage: make train CONFIG=dl/configs/ae.yaml
	$(BIN)/python -m dl.training.train --config $(CONFIG)

eval: ## Evaluate a checkpoint. Usage: make eval CKPT=artifacts/best.pt
	$(BIN)/python -m dl.evaluation.evaluate --ckpt $(CKPT)

export: ## Export a checkpoint to TorchScript/ONNX for the API
	$(BIN)/python -m dl.export.to_onnx --ckpt $(CKPT)

serve: ## Run the FastAPI inference service on :8000
	cd backend && ../$(BIN)/uvicorn app.main:app --reload --port 8000

ui: ## Run the Next.js dashboard on :3000
	cd frontend && npm run dev

up: ## Bring up the whole stack (API + dashboard) with compose
	docker compose -f infra/docker-compose.yml up --build

down: ## Stop the stack
	docker compose -f infra/docker-compose.yml down

clean: ## Remove caches and local artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
