"""Celery application configuration."""

import ssl
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Configure SSL for Redis if using rediss:// (Heroku)
broker_use_ssl = None
redis_backend_use_ssl = None

if settings.redis_url.startswith("rediss://"):
    # Heroku Redis uses TLS, configure SSL settings
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE  # Required for Heroku Redis
    }
    redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

# Create Celery app
celery_app = Celery(
    "whatisonthe_tv",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.content",
        "app.tasks.person",
        "app.tasks.scheduled",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit

    # SSL settings for Redis (Heroku)
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=redis_backend_use_ssl,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Task routing and priorities
    task_routes={
        "app.tasks.content.save_series_full": {"queue": "content", "priority": 5},
        "app.tasks.content.save_movie_full": {"queue": "content", "priority": 5},
        "app.tasks.person.save_person_full": {"queue": "person", "priority": 5},
        "app.tasks.scheduled.*": {"queue": "scheduled", "priority": 1},
    },

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Refresh stale content weekly
    "refresh-stale-content": {
        "task": "app.tasks.scheduled.refresh_stale_content",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
    },
    # Clean up old sync logs monthly
    "cleanup-old-sync-logs": {
        "task": "app.tasks.scheduled.cleanup_old_sync_logs",
        "schedule": crontab(hour=4, minute=0, day_of_month=1),  # 1st of month, 4 AM
    },
}


if __name__ == "__main__":
    celery_app.start()
