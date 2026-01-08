# AI Agent Guidelines - What Is On The TV

Quick reference for AI agents working on this codebase.

## Quick Reference Commands

| Task | Command |
|------|---------|
| Run all services | `make local.run.all` |
| Run backend only | `make local.run` |
| Run frontend only | `make local.run.frontend` |
| Run tests | `make local.test` |
| Run tests with coverage | `make local.test.cov` |
| Lint code | `make lint` |
| Format code | `make format` |
| Create migration | `make local.db.revision MSG="description"` |
| Run migrations | `make local.db.migrate` |

## Key Files

| Purpose | Path |
|---------|------|
| FastAPI app entry | `backend/app/main.py` |
| API routes - Auth | `backend/app/api/auth.py` |
| API routes - Check-ins | `backend/app/api/checkin.py` |
| API routes - Search | `backend/app/api/search.py` |
| Database models | `backend/app/models/` |
| Pydantic schemas | `backend/app/schemas/` |
| TVDB service | `backend/app/services/tvdb.py` |
| Content repository | `backend/app/services/content_repository.py` |
| Celery tasks | `backend/app/tasks/` |
| Frontend API client | `frontend/src/lib/api.ts` |
| Auth store | `frontend/src/lib/stores/auth.ts` |
| Main page | `frontend/src/routes/+page.svelte` |
| Layout | `frontend/src/routes/+layout.svelte` |

## Database Models

| Model | Table | Description |
|-------|-------|-------------|
| User | users | User accounts with auth |
| Content | content | Base for series and movies |
| SeriesDetail | series_detail | Series-specific metadata |
| MovieDetail | movie_detail | Movie-specific metadata |
| Season | season | TV series seasons |
| Episode | episode | Individual episodes |
| Checkin | checkins | User watch records |
| Person | person | Actors, directors, etc. |
| Credit | credit | Person-content relationships |
| Genre | genre | Content genres |

## Implementation Guidelines

### Adding a New API Endpoint

1. Create or update route handler in `backend/app/api/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Register router in `backend/app/main.py` if new file
4. Add frontend API method in `frontend/src/lib/api.ts`
5. Write tests in `backend/tests/`

### Adding a New Model

1. Create model file in `backend/app/models/`
2. Export from `backend/app/models/__init__.py`
3. Create migration: `make local.db.revision MSG="Add model_name table"`
4. Run migration: `make local.db.migrate`
5. Add Pydantic schemas if needed

### Working with TVDB API

- TVDB service: `backend/app/services/tvdb.py`
- Content is fetched on-demand and cached in database
- Use `ContentRepository` for DB-first caching pattern
- Background tasks handle full data sync (genres, credits, episodes)

### Authentication Flow

1. User logs in via `/auth/login` with email/password
2. Backend returns JWT token
3. Frontend stores token in auth store (persisted to localStorage)
4. API requests include `Authorization: Bearer <token>` header
5. Token expiry is checked client-side before requests

### Check-in Flow

1. User searches for content (TVDB API + local cache)
2. User selects movie/series and optionally episode
3. Check-in created with TVDB ID, timestamp, optional notes
4. If content not in DB, basic record created, full sync queued

## Common Tasks

### Fix a Bug in Check-in Logic

1. Review `backend/app/api/checkin.py` for endpoint logic
2. Check `backend/app/schemas/checkin.py` for request/response shapes
3. Check `backend/app/models/checkin.py` for database model
4. Run specific tests: `cd backend && pytest -k "checkin"`
5. Format and lint: `make format && make lint`

### Add a New Frontend Page

1. Create route directory in `frontend/src/routes/`
2. Add `+page.svelte` for the page content
3. Use `$lib/api.ts` for API calls
4. Import from `$lib/stores/auth` for auth state

### Update Database Schema

1. Modify model in `backend/app/models/`
2. Generate migration: `make local.db.revision MSG="Description"`
3. Review generated migration in `backend/alembic/versions/`
4. Apply migration: `make local.db.migrate`
5. Update Pydantic schemas if API shape changes

### Debug Background Task

1. Check task definitions in `backend/app/tasks/`
2. Run worker with logging: `cd backend && celery -A app.workers.celery_app worker --loglevel=debug`
3. Monitor via Flower: `make local.run.flower` (http://localhost:5555)

## Testing Guidelines

- Use pytest with pytest-asyncio for async tests
- Test files go in `backend/tests/`
- Use `httpx.AsyncClient` for API integration tests
- Run with coverage to identify untested code

## Error Handling

### Backend
- Raise `HTTPException` with appropriate status codes
- Use Pydantic for request validation (automatic 422 errors)
- Log errors with Python logging

### Frontend
- API client throws `AuthenticationError` for 401 responses
- Handle errors in component `try/catch` blocks
- Show user-friendly error messages

## Environment Setup

Ensure these are configured before development:

1. Python 3.11 via pyenv
2. Node.js 18+ for frontend
3. Docker for PostgreSQL and Redis (or local installs)
4. TVDB API key in `backend/.env`
