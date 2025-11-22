# WatchLog

Track your TV shows and movies with check-ins, search, and viewing history.

**[🌐 Visit Site](https://www.whatisonthe.tv)**

## Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL (with async SQLAlchemy)
- Redis (caching)
- pytest (testing)

**Frontend:**
- SvelteKit (coming soon)
- TypeScript

**External APIs:**
- TheTVDB API for show/movie metadata

## Project Structure

```
watchlog/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core config and utilities
│   │   ├── db/           # Database and Redis setup
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── tests/            # pytest tests
│   ├── requirements.txt  # Production dependencies
│   └── requirements-dev.txt  # Development dependencies
├── frontend/             # SvelteKit app (coming soon)
├── docker-compose.yml    # Postgres + Redis
└── Makefile             # Development commands
```

## Prerequisites

- Python 3.11 (managed via pyenv)
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Make

## Quick Start

### 1. Clone and Setup

```bash
cd ~/Documents/Code/watchlog

# Ensure you're using Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Setup everything (install deps + start databases)
make setup
```

### 2. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env and add your TVDB API key (get one from https://thetvdb.com/)
```

### 3. Run Development Server

```bash
# Start backend (from project root)
make dev

# Backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Makefile Commands

```bash
make help          # Show all available commands
make setup         # Install dependencies and start databases
make install       # Install production dependencies
make install-dev   # Install development dependencies
make db-up         # Start PostgreSQL and Redis
make db-down       # Stop databases
make db-reset      # Reset databases (destroys all data)
make dev           # Start FastAPI development server
make test          # Run tests
make test-cov      # Run tests with coverage report
make lint          # Run linters (ruff, mypy)
make format        # Format code (black, ruff)
make clean         # Clean up cache files
```

## Development

### Backend Development

```bash
# Activate virtual environment
source venv/bin/activate

# Start databases
make db-up

# Run development server
make dev

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Lint code
make lint
```

### Database

PostgreSQL runs in Docker on port 5432:
- Database: `watchlog`
- User: `watchlog`
- Password: `watchlog`

Redis runs in Docker on port 6379.

### API Documentation

Once the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing

Tests are written with pytest and include:
- Unit tests
- Integration tests
- Coverage reporting

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
cd backend && pytest tests/test_main.py

# Run tests matching a pattern
cd backend && pytest -k "test_health"
```

## API Endpoints

### Current Endpoints

- `GET /` - Root endpoint with app info
- `GET /health` - Health check

### Coming Soon

- `POST /checkins` - Create a check-in for a show/movie
- `GET /checkins` - List all check-ins
- `GET /search` - Search TVDB for shows/movies
- `GET /shows/{id}` - Get show details
- `GET /movies/{id}` - Get movie details

## Self-Hosting

This application is designed to be easily self-hosted on a cheap VPS.

### Recommended Providers
- Hetzner Cloud (~€4/month)
- DigitalOcean ($6/month)
- Vultr, Linode, etc.

### Deployment (Coming Soon)
- Docker Compose for production
- Caddy for HTTPS
- Systemd service files

## External Integrations (Future)

- Apple TV+ viewing history
- Netflix viewing history
- Amazon Prime viewing history

*Note: These integrations depend on available APIs/methods*

## License

Personal project - use as you wish!

## Author

Stephen McCullough
