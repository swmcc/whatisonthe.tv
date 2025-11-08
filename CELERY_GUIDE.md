# Celery Background Tasks Guide

This project uses **Celery + Redis** for production-ready async background processing with aggressive caching.

## 🎯 What Does This Do?

### The Flow:
```
User requests "Breaking Bad" details
    ↓
1. Check PostgreSQL database first
    ↓
2. Found in DB and < 7 days old? → Return immediately (FAST!)
    ↓
3. Not found or stale? → Get from TVDB API
    ↓
4. Return API data to user immediately (don't make them wait!)
    ↓
5. Queue background Celery task to save/update in DB
    ↓
6. Worker processes task async
    ↓
7. Next request for same show is instant (from DB)
```

### Benefits:
- ✅ **Fast responses** - User never waits for DB writes
- ✅ **Always fresh** - Stale data refreshed automatically
- ✅ **Automatic sync** - Weekly refresh of old content
- ✅ **Production ready** - Retry logic, error handling, monitoring
- ✅ **Scalable** - Add more workers as needed

---

## 🚀 Quick Start

### Running Locally

**Option 1: All services together**
```bash
make dev-all
# Runs: Backend API + Frontend + Celery Worker
```

**Option 2: Separate terminals (recommended for development)**
```bash
# Terminal 1: Backend API
make dev-backend

# Terminal 2: Frontend
make dev-frontend

# Terminal 3: Celery Worker
make dev-worker

# Terminal 4 (optional): Celery Beat (scheduled tasks)
make dev-beat

# Terminal 5 (optional): Flower monitoring UI
make dev-flower
# Open http://localhost:5555 to see tasks
```

---

## 📦 What Was Implemented

### 1. **Content Repository** (`app/services/content_repository.py`)
- DB-first caching strategy
- Automatic staleness detection (7 days for content, 14 for people)
- Returns cached data when fresh, API data when stale
- Queues background sync tasks

### 2. **Celery Tasks** (`app/tasks/`)

**Content Tasks** (`content.py`):
- `save_series_full(tvdb_id)` - Save complete series with credits, genres, aliases
- `save_movie_full(tvdb_id)` - Save complete movie data

**Person Tasks** (`person.py`):
- `save_person_full(tvdb_id)` - Save person with biography, filmography

**Scheduled Tasks** (`scheduled.py`):
- `refresh_stale_content()` - Weekly refresh (Sunday 3 AM)
- `refresh_stale_people()` - Weekly refresh
- `cleanup_old_sync_logs()` - Monthly cleanup (1st of month, 4 AM)

### 3. **API Endpoints** (Updated)
- `/search` - Search TVDB (always fresh, not cached)
- `/series/{id}` - Get series (DB-first, async cache)
- `/movie/{id}` - Get movie (DB-first, async cache)
- `/person/{id}` - Get person (DB-first, async cache)

### 4. **Monitoring**
- Flower dashboard at `http://localhost:5555`
- View active tasks, completed tasks, failures
- See worker health and performance

---

## 🔧 Configuration

### Celery Settings (`app/workers/celery_app.py`)

**Task Routing:**
- `content` queue: Series/movie saves (priority 5)
- `person` queue: Person saves (priority 5)
- `scheduled` queue: Maintenance tasks (priority 1)

**Retry Logic:**
- Max 3 retries per task
- Automatic retry on failure
- Exponential backoff

**Scheduled Tasks:**
```python
# Sunday 3 AM - Refresh stale content
'refresh-stale-content': crontab(hour=3, minute=0, day_of_week=0)

# 1st of month, 4 AM - Cleanup logs
'cleanup-old-sync-logs': crontab(hour=4, minute=0, day_of_month=1)
```

---

## 💡 How It Works in Practice

### Example: User Views Breaking Bad

**First Request** (not in DB):
```
1. User requests /series/81189
2. DB check → Not found
3. TVDB API call → Returns data
4. User gets response immediately (200ms)
5. Background: save_series_full.delay(81189) queued
6. Worker picks up task and saves to DB
```

**Second Request** (in DB, fresh):
```
1. User requests /series/81189
2. DB check → Found, synced 2 days ago
3. User gets response from DB (50ms) ← 4x faster!
```

**Third Request** (in DB, stale - 8 days old):
```
1. User requests /series/81189
2. DB check → Found but 8 days old
3. TVDB API call → Returns fresh data
4. User gets response immediately (200ms)
5. Background: save_series_full.delay(81189) queued to update
```

---

## 📊 Monitoring Tasks

### Using Flower (Web UI)
```bash
make dev-flower
# Open http://localhost:5555
```

See:
- Active tasks currently running
- Completed tasks history
- Failed tasks with error messages
- Worker status and performance
- Task execution time graphs

### Using Command Line
```bash
# See active workers
celery -A app.workers.celery_app inspect active

# See stats
celery -A app.workers.celery_app inspect stats

# Purge all tasks (DANGER!)
celery -A app.workers.celery_app purge
```

---

## 🎛️ Advanced Usage

### Manual Task Triggering

```python
# In Python shell or API endpoint
from app.tasks.content import save_series_full

# Queue a task
result = save_series_full.delay(81189)

# Check task status
result.ready()  # Is it done?
result.get()    # Get result (blocking)
```

### Scaling Workers

```bash
# Run 4 worker processes
celery -A app.workers.celery_app worker --concurrency=4

# Run multiple workers on different machines
# Just point them all at the same Redis instance
```

### Priority Tasks

```python
# High priority (user-requested)
save_series_full.apply_async(args=[81189], priority=9)

# Low priority (background refresh)
save_series_full.apply_async(args=[81189], priority=1)
```

---

## 🐛 Troubleshooting

### Worker not processing tasks?
```bash
# Check if worker is running
celery -A app.workers.celery_app inspect active

# Check Redis connection
redis-cli ping  # Should return "PONG"

# Check for errors in worker logs
make dev-worker  # See logs in terminal
```

### Tasks failing?
```bash
# Check Flower for error messages
make dev-flower

# Or check sync_log table in DB
psql watchlog -c "SELECT * FROM sync_log WHERE sync_status='failed' ORDER BY synced_at DESC LIMIT 10;"
```

### DB not being populated?
- Make sure worker is running (`make dev-worker`)
- Check worker logs for errors
- Verify Redis is running (`redis-cli ping`)
- Check sync_log table for failures

---

## 🚢 Production Deployment

### On Your Server (No Docker)

**1. Install systemd services** (see example in main README)

**2. Start services**
```bash
sudo systemctl start whatisonthe-api
sudo systemctl start whatisonthe-worker
sudo systemctl start whatisonthe-beat
sudo systemctl enable whatisonthe-api
sudo systemctl enable whatisonthe-worker
sudo systemctl enable whatisonthe-beat
```

**3. Monitor**
```bash
# View logs
journalctl -u whatisonthe-worker -f

# Check status
systemctl status whatisonthe-worker
```

---

## 📈 Performance

### Expected Performance

**Cold start (not in DB):**
- API request: ~200-300ms
- Background save: 500-1000ms (user doesn't wait)

**Warm (in DB, fresh):**
- API request: ~50-100ms (4x faster!)

**Database Growth:**
- ~5KB per series entry
- ~3KB per movie entry
- ~2KB per person entry
- 100 series = ~500KB
- 1000 series = ~5MB

### Caching Strategy

- **Search results**: Not cached (always fresh from API)
- **Detail views**: Aggressively cached (7 day TTL)
- **People**: Cached (14 day TTL)
- **Automatic refresh**: Weekly for stale data

---

## 🎓 Next Steps

1. **View a show** - See it get cached in real-time
2. **Check Flower** - Watch tasks being processed
3. **View DB** - See data populating
4. **Request again** - See blazing fast cached response
5. **Wait 8 days** - Watch automatic refresh kick in

---

## Questions?

- Tasks not running? Check worker is started
- Data not saving? Check sync_log table for errors
- Want to customize? Edit `app/workers/celery_app.py`
- Need help? Check Flower dashboard for insights

**The system is production-ready and will scale with you!** 🚀
