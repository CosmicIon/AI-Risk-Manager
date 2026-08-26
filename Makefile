.PHONY: help up down ps logs backend-dev dashboard-dev test lint format migrate seed clean

help:
	@echo "AI Risk Manager — Development Commands"
	@echo "======================================"
	@echo "  make up            - Spin up all infrastructure containers (Docker Compose)"
	@echo "  make down          - Stop and remove infrastructure containers"
	@echo "  make ps            - Check status of running containers"
	@echo "  make logs          - Tail container logs"
	@echo "  make backend-dev   - Run FastAPI backend locally with hot-reload"
	@echo "  make dashboard-dev - Run Next.js dashboard locally"
	@echo "  make test          - Run backend test suite with coverage"
	@echo "  make lint          - Run ruff linter and mypy type checks"
	@echo "  make format        - Format code using ruff"
	@echo "  make migrate       - Apply database migrations (alembic upgrade head)"
	@echo "  make seed          - Seed development database"
	@echo "  make clean         - Clean cache and temporary files"

up:
	docker compose -f infra/docker/docker-compose.yml up -d

down:
	docker compose -f infra/docker/docker-compose.yml down -v

ps:
	docker compose -f infra/docker/docker-compose.yml ps

logs:
	docker compose -f infra/docker/docker-compose.yml logs -f

backend-dev:
	cd backend && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dashboard-dev:
	cd dashboard && npm run dev

test:
	cd backend && pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	cd backend && ruff check src/ tests/ && mypy src/

format:
	cd backend && ruff format src/ tests/

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python scripts/seed_db.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
