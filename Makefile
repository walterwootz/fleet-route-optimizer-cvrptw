.PHONY: help up down restart logs clean db-shell migrate test

help:
	@echo "RailFleet Manager - Makefile Commands"
	@echo "======================================"
	@echo "make up          - Start all services"
	@echo "make down        - Stop all services"
	@echo "make restart     - Restart all services"
	@echo "make logs        - View logs"
	@echo "make clean       - Remove containers and volumes"
	@echo "make db-shell    - Open PostgreSQL shell"
	@echo "make migrate     - Run database migrations"
	@echo "make test        - Run tests"

up:
	@echo "Starting RailFleet Manager..."
	cd docker && docker-compose up -d
	@echo "Services started!"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo "pgAdmin: http://localhost:5050"

down:
	@echo "Stopping RailFleet Manager..."
	cd docker && docker-compose down

restart:
	@echo "Restarting RailFleet Manager..."
	cd docker && docker-compose restart

logs:
	cd docker && docker-compose logs -f

logs-backend:
	cd docker && docker-compose logs -f backend

logs-postgres:
	cd docker && docker-compose logs -f postgres

clean:
	@echo "Removing containers and volumes..."
	cd docker && docker-compose down -v
	@echo "Cleaned!"

db-shell:
	docker exec -it railfleet-postgres psql -U railfleet -d railfleet_db

migrate:
	@echo "Running database migrations..."
	docker exec -it railfleet-backend alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	docker exec -it railfleet-backend alembic revision --autogenerate -m "$$msg"

test:
	@echo "Running tests..."
	docker exec -it railfleet-backend pytest

install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

dev:
	@echo "Starting development server..."
	uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
