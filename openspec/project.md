# What Is On The TV - Project Conventions

## Overview

WatchLog (What Is On The TV) is a personal TV and movie tracking application. Users can search for TV shows and movies via TheTVDB API, check in when they watch content, and maintain a viewing history. The app supports public profile pages for sharing watch activity.

## Tech Stack

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Database:** PostgreSQL with async SQLAlchemy
- **Cache:** Redis
- **Task Queue:** Celery with Flower monitoring
- **Authentication:** JWT via python-jose, bcrypt for password hashing
- **External APIs:** TheTVDB API v4 for content metadata

### Frontend
- **Framework:** SvelteKit
- **Language:** TypeScript
- **Styling:** Tailwind CSS with @tailwindcss/forms
- **Build:** Vite

### Infrastructure
- **Deployment:** Heroku
- **CI/CD:** GitHub Actions

## Architecture

```
whatisonthe.tv/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI route handlers
│   │   │   ├── auth.py    # Authentication endpoints
│   │   │   ├── checkin.py # Check-in CRUD operations
│   │   │   └── search.py  # Search and content retrieval
│   │   ├── core/          # Config, security, dependencies
│   │   ├── db/            # Database and Redis setup
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── services/      # Business logic (TVDB, content repo)
│   │   ├── tasks/         # Celery background tasks
│   │   └── workers/       # Celery worker configuration
│   ├── alembic/           # Database migrations
│   └── tests/             # pytest tests
├── frontend/
│   └── src/
│       ├── lib/           # Shared utilities and components
│       │   ├── api.ts     # API client
│       │   ├── stores/    # Svelte stores
│       │   └── components/
│       └── routes/        # SvelteKit pages
└── openspec/              # This specification directory
```

### Key Design Patterns

1. **DB-First Caching:** Content is cached locally after first API fetch. Stale data (>7 days) triggers background sync.
2. **Background Tasks:** Full content sync (genres, credits, episodes) happens via Celery after initial basic save.
3. **TVDB IDs as External Keys:** API endpoints use TVDB IDs; internal database uses auto-increment IDs.

## Git Commit Conventions

Use gitmoji format with emoji at the start of commit messages:

| Emoji | Code | Usage |
|-------|------|-------|
| :sparkles: | `:sparkles:` | New feature |
| :bug: | `:bug:` | Bug fix |
| :recycle: | `:recycle:` | Refactor code |
| :lipstick: | `:lipstick:` | UI/style updates |
| :zap: | `:zap:` | Performance improvement |
| :lock: | `:lock:` | Security fix |
| :wrench: | `:wrench:` | Configuration changes |
| :memo: | `:memo:` | Documentation |
| :white_check_mark: | `:white_check_mark:` | Add/update tests |
| :construction: | `:construction:` | Work in progress |
| :rocket: | `:rocket:` | Deployment |
| :art: | `:art:` | Code structure/format |
| :fire: | `:fire:` | Remove code/files |
| :heavy_plus_sign: | `:heavy_plus_sign:` | Add dependency |
| :heavy_minus_sign: | `:heavy_minus_sign:` | Remove dependency |
| :arrow_up: | `:arrow_up:` | Upgrade dependency |

**Examples:**
```
:sparkles: Add public profile pages for sharing check-ins
:bug: Fix authentication state desync causing invalid credentials errors
:recycle: Refactor content repository for better caching
```

## Code Conventions

### Python (Backend)

- **Style:** Black formatter, Ruff linter
- **Type Hints:** Required; enforce with mypy
- **Docstrings:** Google style for functions and classes
- **Async:** Use async/await for database and external API calls
- **Naming:**
  - snake_case for functions and variables
  - PascalCase for classes
  - SCREAMING_SNAKE_CASE for constants

### TypeScript (Frontend)

- **Style:** ESLint with Svelte plugin
- **Types:** Strict mode enabled
- **Naming:**
  - camelCase for functions and variables
  - PascalCase for components and types
- **API Calls:** Always through `$lib/api.ts` client

### Database

- **Migrations:** Alembic with autogenerate
- **Naming:** snake_case for tables and columns
- **Relationships:** Use SQLAlchemy's ORM relationships with lazy="selectin" for eager loading

## Commands

### Development

```bash
# Full setup (installs deps)
make setup

# Start all services (backend, frontend, Celery worker)
make local.run.all

# Start individual services
make local.run          # Backend only (uvicorn)
make local.run.frontend # Frontend only (vite)
make local.run.worker   # Celery worker
make local.run.beat     # Celery beat scheduler
make local.run.flower   # Flower monitoring UI
```

### Database

```bash
make local.db.migrate              # Run migrations
make local.db.downgrade            # Rollback last migration
make local.db.revision MSG="desc"  # Create new migration
```

### Testing

```bash
make local.test      # Run all tests
make local.test.cov  # Run with coverage report

# Run specific tests
cd backend && pytest tests/test_main.py
cd backend && pytest -k "test_health"
```

### Code Quality

```bash
make lint      # Run ruff + mypy
make lint.fix  # Auto-fix issues
make format    # Format with black + ruff
make clean     # Remove cache files
```

### Frontend

```bash
cd frontend
npm run dev       # Development server
npm run build     # Production build
npm run check     # Type checking
npm run lint      # ESLint
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql+asyncpg://watchlog:watchlog@localhost:5432/watchlog
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
TVDB_API_KEY=your-tvdb-api-key
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
DEBUG=true
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

## API Documentation

When the backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
