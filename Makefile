.DEFAULT_GOAL := help
COMPOSE := docker compose -f infra/compose/docker-compose.yml

help: ## Show the available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install Python and Node dependencies
	uv sync --all-extras
	cd apps/web && npm install

up: ## Start Postgres and Redis
	$(COMPOSE) up -d
	@echo "waiting for postgres..." && until $(COMPOSE) exec -T db pg_isready -U corredor >/dev/null 2>&1; do sleep 1; done

down: ## Stop the infrastructure containers
	$(COMPOSE) down

reset: ## Destroy and recreate the database volume
	$(COMPOSE) down -v && $(MAKE) up && $(MAKE) migrate && $(MAKE) seed

migrate: ## Apply database migrations
	cd apps/api && uv run alembic upgrade head

revision: ## Autogenerate a migration: make revision m="add x"
	cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

seed: ## Load the demo tenant, ramos and sample book of business
	uv run python -m corredor.scripts.seed

api: ## Run the API with reload
	uv run uvicorn corredor.main:app --reload --port 8000

web: ## Run the public web app
	cd apps/web && npm run dev

test: ## Run the test suite
	uv run pytest

lint: ## Lint and type-check
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy apps/api/src packages/ml/src

format: ## Auto-format
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: help install up down reset migrate revision seed api web test lint format
