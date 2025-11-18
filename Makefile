APP_NAME=whatisonthe.tv
RAILS_ENV ?= development

GREEN := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET := $(shell tput -Txterm sgr0)

.DEFAULT_GOAL := help

# -----------------------------
# 🧩 Local Development
# -----------------------------

local.run: ## Run the FastAPI backend
	@echo "$(GREEN)==> Running $(APP_NAME) backend...$(RESET)"
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

local.run.frontend: ## Run the SvelteKit frontend
	@echo "$(GREEN)==> Running $(APP_NAME) frontend...$(RESET)"
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

local.run.all: ## Start backend, frontend, and Celery worker concurrently
	@echo "$(GREEN)==> Starting all services (backend, frontend, worker)...$(RESET)"
	@trap 'kill 0' EXIT; \
	(cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev -- --host 0.0.0.0 --port 5173) & \
	(cd backend && celery -A app.workers.celery_app worker --loglevel=info -Q celery,content,person,scheduled) & \
	wait

local.run.worker: ## Start Celery worker for background tasks
	@echo "$(GREEN)==> Starting Celery worker...$(RESET)"
	cd backend && celery -A app.workers.celery_app worker --loglevel=info -Q celery,content,person,scheduled

local.run.beat: ## Start Celery beat scheduler for periodic tasks
	@echo "$(GREEN)==> Starting Celery beat scheduler...$(RESET)"
	cd backend && celery -A app.workers.celery_app beat --loglevel=info

local.run.flower: ## Start Flower monitoring UI (http://localhost:5555)
	@echo "$(GREEN)==> Starting Flower monitoring UI...$(RESET)"
	cd backend && celery -A app.workers.celery_app flower

local.setup: ## Complete setup: install deps
	@echo "$(GREEN)==> Setting up $(APP_NAME)...$(RESET)"
	@echo "$(YELLOW)==> Installing backend dependencies...$(RESET)"
	cd backend && pip install -r requirements-dev.txt
	@echo "$(YELLOW)==> Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(GREEN)✅ Setup complete!$(RESET)"
	@echo "$(GREEN)==> Run 'make local.run.all' to start all services$(RESET)"

local.install: ## Install production dependencies
	@echo "$(GREEN)==> Installing production dependencies...$(RESET)"
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

local.install.dev: ## Install development dependencies
	@echo "$(GREEN)==> Installing development dependencies...$(RESET)"
	cd backend && pip install -r requirements-dev.txt
	cd frontend && npm install

local.db.migrate: ## Run database migrations
	@echo "$(GREEN)==> Running database migrations...$(RESET)"
	cd backend && python3 -m alembic upgrade head

local.db.downgrade: ## Rollback last migration
	@echo "$(YELLOW)==> Rolling back last migration...$(RESET)"
	cd backend && python3 -m alembic downgrade -1

local.db.revision: ## Create new migration (use MSG="description")
	@echo "$(GREEN)==> Creating new migration...$(RESET)"
	cd backend && python3 -m alembic revision --autogenerate -m "$(MSG)"

local.test: ## Run backend tests
	@echo "$(GREEN)==> Running tests...$(RESET)"
	cd backend && pytest

local.test.cov: ## Run tests with coverage report
	@echo "$(GREEN)==> Running tests with coverage...$(RESET)"
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

console: ## Start Python console with app context
	@echo "$(GREEN)==> Starting Python console...$(RESET)"
	cd backend && python3

# -----------------------------
# 🧹 Code Quality
# -----------------------------

lint: ## Run linters (ruff + mypy)
	@echo "$(GREEN)==> Running linters...$(RESET)"
	cd backend && ruff check app tests
	cd backend && mypy app

lint.fix: ## Auto-fix linting issues
	@echo "$(GREEN)==> Auto-fixing linting issues...$(RESET)"
	cd backend && ruff check --fix app tests
	cd backend && black app tests

format: ## Format code with black and ruff
	@echo "$(GREEN)==> Formatting code...$(RESET)"
	cd backend && black app tests
	cd backend && ruff check --fix app tests

clean: ## Clean up cache and generated files
	@echo "$(GREEN)==> Cleaning up cache files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "$(GREEN)✅ Cleaned up cache files$(RESET)"

# -----------------------------
# 🧰 Meta
# -----------------------------

help: ## Show all available make targets
	@echo "$(GREEN)Available targets:$(RESET)"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  %-25s %s\n", $$1, $$2}'

# Backwards compatibility aliases (legacy targets without local. prefix)
dev: local.run
dev-backend: local.run
dev-frontend: local.run.frontend
dev-all: local.run.all
dev-worker: local.run.worker
dev-beat: local.run.beat
dev-flower: local.run.flower
setup: local.setup
install: local.install
install-dev: local.install.dev
db-migrate: local.db.migrate
db-upgrade: local.db.migrate
db-downgrade: local.db.downgrade
db-revision: local.db.revision
test: local.test
test-cov: local.test.cov
