# What Is On The TV - Project Context

## Project Overview
A watch logging and tracking application for TV shows and movies. Users can track what they're watching, log their viewing history, and get insights about their viewing habits.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **ORM**: SQLAlchemy (likely)
- **Testing**: pytest
- **Linting**: ruff, mypy
- **Formatting**: black

### Frontend
- **Framework**: SvelteKit 2.x
- **Build Tool**: Vite 5.x
- **Language**: TypeScript
- **UI**: Svelte 4.x

## Development Workflow

### Setup
```bash
make setup              # Install deps and start databases
```

### Running Servers
```bash
make dev-all            # Run both backend and frontend
make dev-backend        # Backend only (port 8000)
make dev-frontend       # Frontend only (port 5173)
```

### Testing
```bash
make test              # Run tests
make test-cov          # Run with coverage
```

### Code Quality
```bash
make lint              # Run linters
make format            # Format code
```

## Project Structure
```
.
├── backend/           # FastAPI application
│   ├── app/          # Main application code
│   └── tests/        # Backend tests
├── frontend/         # SvelteKit application
│   └── src/
│       └── routes/   # SvelteKit routes
├── docker-compose.yml # PostgreSQL + Redis
└── Makefile          # Development commands
```

## Coding Guidelines

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for modules and functions
- Keep functions focused and single-purpose
- Use black for formatting, ruff for linting

### TypeScript/Svelte (Frontend)
- Use TypeScript for type safety
- Follow Svelte best practices
- Keep components small and reusable
- Use descriptive variable names

### Git Workflow
- Write clear, descriptive commit messages
- Use conventional commit format with emojis
- Include co-author attribution for AI-assisted commits
- Keep commits focused on single concerns

## Environment Variables
- Backend: Configure via `.env` file (see backend docs)
- Frontend: Use `VITE_` prefix for environment variables

## Important Notes
- Always run tests before committing
- Database runs in Docker containers
- Frontend connects to backend at `http://localhost:8000`
- Use `make help` to see all available commands
