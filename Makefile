.PHONY: up down build migrate seed logs reset-db worker shell-api shell-db dev

# Start full stack
up:
	docker compose up --build -d
	@echo "Stack is up. Open http://localhost"

# Start development mode (with hot reload)
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
	@echo "Dev stack is up. Open http://localhost"

# Stop stack
down:
	docker compose down

# Build images only
build:
	docker compose build

# Run Alembic migrations
migrate:
	docker compose exec api sh -c "cd /app && PYTHONPATH=/app alembic upgrade head"
	@echo "Migrations applied"

# Seed database
seed:
	docker compose exec api python scripts/seed_wcag.py
	docker compose exec api python scripts/seed_dev.py
	@echo "Database seeded"

# Tail logs
logs:
	docker compose logs -f api worker

# Full reset (destroys all data)
reset-db:
	docker compose down -v
	docker compose up --build -d
	@sleep 5
	@$(MAKE) migrate
	@$(MAKE) seed
	@echo "Database reset complete"

# Open shell inside api container
shell-api:
	docker compose exec api bash

# Open psql shell
shell-db:
	docker compose exec postgres psql -U a11y -d accessibility_db

# Start celery worker (dev)
worker:
	docker compose exec worker celery -A tasks.celery_app worker --loglevel=info

