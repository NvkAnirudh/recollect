# Recollect developer commands. `make help` lists them.
.DEFAULT_GOAL := help
SHELL := /bin/bash

.PHONY: help setup db db-stop db-reset db-new api web check check-backend check-frontend fmt test

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies and git hooks (run once after cloning)
	cd backend && uv sync
	cd frontend && pnpm install
	pre-commit install

db: ## Start local Supabase (Postgres, Auth, Storage) and print its keys
	supabase start

db-stop: ## Stop local Supabase
	supabase stop

db-reset: ## Recreate the local database from migrations + seed
	supabase db reset

db-new: ## Create a migration: make db-new name=add_reels
	@test -n "$(name)" || (echo "usage: make db-new name=<snake_case_name>" && exit 1)
	supabase migration new $(name)

api: ## Run the API with reload on :8000
	cd backend && uv run uvicorn recollect.api.main:app --reload --port 8000

web: ## Run the web app on :3000
	cd frontend && pnpm dev

fmt: ## Format all code
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && pnpm format

test: ## Run all tests
	cd backend && uv run pytest
	cd frontend && pnpm test

check-backend: ## Backend: format check, lint, types, tests (same as CI)
	cd backend && uv run ruff format --check . && uv run ruff check . && uv run pyright && uv run pytest

check-frontend: ## Frontend: format check, lint, types, tests, build (same as CI)
	cd frontend && pnpm format:check && pnpm lint && pnpm typecheck && pnpm test:coverage && pnpm build

check: check-backend check-frontend ## Everything CI runs, except the database and image jobs
	actionlint
	pre-commit run --all-files
