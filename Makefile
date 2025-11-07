.PHONY: help install install-dev setup db-up db-down db-reset dev test test-cov lint format clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	cd backend && pip install -r requirements.txt

install-dev: ## Install development dependencies
	cd backend && pip install -r requirements-dev.txt

setup: install-dev db-up ## Complete setup: install deps and start databases
	@echo "✅ Setup complete!"
	@echo "Run 'make dev' to start the development server"

db-up: ## Start PostgreSQL and Redis
	docker-compose up -d
	@echo "⏳ Waiting for databases to be ready..."
	@sleep 3
	@echo "✅ Databases are ready"

db-down: ## Stop PostgreSQL and Redis
	docker-compose down

db-reset: ## Reset databases (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d
	@sleep 3
	@echo "✅ Databases reset"

dev: ## Start development server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

test: ## Run tests
	cd backend && pytest

test-cov: ## Run tests with coverage report
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linters
	cd backend && ruff check app tests
	cd backend && mypy app

format: ## Format code with black and ruff
	cd backend && black app tests
	cd backend && ruff check --fix app tests

clean: ## Clean up cache and generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "✅ Cleaned up cache files"
