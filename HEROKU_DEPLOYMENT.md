# Heroku Deployment Guide

This guide walks through deploying What Is On The TV to Heroku.

## Prerequisites

- Heroku CLI installed: `brew install heroku/brew/heroku`
- Heroku account
- TVDB API credentials (API key and PIN)

## Initial Setup

### 1. Create Heroku App

```bash
heroku create whatisonthe-tv
```

Or use an existing app:
```bash
heroku git:remote -a whatisonthe-tv
```

### 2. Add Heroku Add-ons

Add PostgreSQL database (mini tier):
```bash
heroku addons:create heroku-postgresql:mini
```

Add Redis (mini tier):
```bash
heroku addons:create heroku-redis:mini
```

### 3. Set Environment Variables

```bash
# Security
heroku config:set SECRET_KEY=$(openssl rand -hex 32)

# TVDB API credentials
heroku config:set TVDB_API_KEY=your-api-key-here
heroku config:set TVDB_PIN=your-pin-here

# CORS (update with your actual domain)
heroku config:set CORS_ORIGINS=https://whatisonthe-tv.herokuapp.com,https://www.yourdomain.com

# Optional: Enable debug mode (not recommended for production)
heroku config:set DEBUG=false
```

### 4. Deploy

```bash
git push heroku main
```

### 5. Scale Dynos

Enable web and worker dynos:
```bash
heroku ps:scale web=1 worker=1
```

## Architecture

The app uses the following Heroku resources:

- **Web Dyno**: Runs FastAPI backend with Uvicorn, serves frontend static files
- **Worker Dyno**: Runs Celery worker for background tasks
- **PostgreSQL**: Database for content and user data
- **Redis**: Message broker for Celery and caching
- **Node.js Buildpack**: Builds SvelteKit frontend
- **Python Buildpack**: Installs Python dependencies

## Build Process

Heroku uses multi-buildpack approach:

1. **Node.js buildpack**: Builds frontend
   - Runs `npm install` in frontend directory
   - Runs `npm run build` to create production build
   - Outputs to `frontend/build/`

2. **Python buildpack**: Installs backend
   - Installs Python dependencies from `requirements.txt`
   - Runs release phase (migrations)

3. **FastAPI serves frontend**:
   - Static files served from `frontend/build/`
   - SPA routing handled with fallback to `index.html`
   - API routes prefixed (auth, checkins, search, health)

## Procfile Processes

- `release`: Runs database migrations before deployment
- `web`: FastAPI backend server (also serves frontend)
- `worker`: Celery worker for background sync tasks

## Database Migrations

Migrations run automatically during the release phase via `bin/release.sh`.

To manually run migrations:
```bash
heroku run bash bin/release.sh
```

## Monitoring

View logs:
```bash
heroku logs --tail
```

View dyno status:
```bash
heroku ps
```

Monitor Celery worker:
```bash
heroku logs --tail --dyno worker
```

## Scaling

Scale web dynos:
```bash
heroku ps:scale web=2
```

Scale worker dynos:
```bash
heroku ps:scale worker=2
```

## Environment Variables

The app automatically detects and uses Heroku environment variables:

- `DATABASE_URL`: Provided by heroku-postgresql
- `REDIS_URL`: Provided by heroku-redis
- `PORT`: Provided by Heroku for web dyno
- `SECRET_KEY`: JWT secret (set manually)
- `TVDB_API_KEY`: TVDB API key (set manually)
- `TVDB_PIN`: TVDB PIN (set manually)
- `CORS_ORIGINS`: Comma-separated list of allowed origins (set manually)

## Troubleshooting

### Check configuration
```bash
heroku config
```

### Restart dynos
```bash
heroku restart
```

### Check database
```bash
heroku pg:info
heroku pg:psql
```

### Check Redis
```bash
heroku redis:info
heroku redis:cli
```

### Run interactive shell
```bash
heroku run bash
```

## Cost Estimation (Mini Tier)

- Heroku Postgres Mini: $5/month
- Heroku Redis Mini: $3/month
- Basic Web Dyno: ~$7/month
- Basic Worker Dyno: ~$7/month

**Total**: ~$22/month for basic tier

## Upgrading

To upgrade add-ons:
```bash
heroku addons:upgrade heroku-postgresql:standard-0
heroku addons:upgrade heroku-redis:premium-0
```

## Frontend Configuration

The frontend is built and served by the backend. The build process:

1. Heroku's Node.js buildpack runs `npm install && npm run build` in the frontend directory
2. SvelteKit builds static files to `frontend/build/`
3. FastAPI serves these files and handles SPA routing
4. API calls go to the same domain (no CORS issues)

**No separate frontend deployment needed!** Everything is served from one Heroku app.

## Security Checklist

- [ ] Set strong SECRET_KEY
- [ ] Disable DEBUG in production
- [ ] Configure CORS_ORIGINS with actual domain
- [ ] Keep TVDB credentials secure
- [ ] Enable HTTPS only
- [ ] Review database access logs
- [ ] Set up monitoring alerts

## Useful Commands

```bash
# View recent logs
heroku logs --tail -n 100

# Open app in browser
heroku open

# Run Python shell
heroku run python

# Run database migrations
heroku run bash bin/release.sh

# Check Celery status
heroku logs --tail --dyno worker

# Restart specific dyno type
heroku ps:restart web
heroku ps:restart worker
```
