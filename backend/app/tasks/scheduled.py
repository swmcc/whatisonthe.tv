"""Scheduled Celery tasks for maintenance."""

from datetime import datetime, timedelta

from sqlalchemy import delete, select

from app.db.database import AsyncSessionLocal
from app.models.content import Content
from app.models.person import Person
from app.models.sync_log import SyncLog
from app.workers.celery_app import celery_app
from app.tasks.content import save_series_full, save_movie_full
from app.tasks.person import save_person_full


@celery_app.task
def refresh_stale_content():
    """
    Refresh content that hasn't been synced in 7+ days.

    This runs weekly (Sunday 3 AM) to keep popular content fresh.
    """
    import asyncio
    return asyncio.run(_refresh_stale_content_async())


async def _refresh_stale_content_async():
    """Async implementation of refresh_stale_content."""
    async with AsyncSessionLocal() as db:
        threshold = datetime.utcnow() - timedelta(days=7)

        # Find stale content
        stmt = (
            select(Content)
            .where(
                (Content.last_synced_at < threshold) |
                (Content.last_synced_at.is_(None))
            )
            .limit(100)  # Process 100 at a time
        )
        result = await db.execute(stmt)
        stale_content = result.scalars().all()

        # Queue refresh tasks
        refreshed_count = 0
        for content in stale_content:
            if content.content_type == "series":
                save_series_full.delay(content.tvdb_id)
            elif content.content_type == "movie":
                save_movie_full.delay(content.tvdb_id)
            refreshed_count += 1

        return {
            "status": "success",
            "refreshed_count": refreshed_count,
            "message": f"Queued {refreshed_count} content items for refresh"
        }


@celery_app.task
def refresh_stale_people():
    """
    Refresh people that haven't been synced in 14+ days.

    This runs weekly to keep person data fresh.
    """
    import asyncio
    return asyncio.run(_refresh_stale_people_async())


async def _refresh_stale_people_async():
    """Async implementation of refresh_stale_people."""
    async with AsyncSessionLocal() as db:
        threshold = datetime.utcnow() - timedelta(days=14)

        # Find stale people
        stmt = (
            select(Person)
            .where(
                (Person.last_synced_at < threshold) |
                (Person.last_synced_at.is_(None))
            )
            .limit(100)  # Process 100 at a time
        )
        result = await db.execute(stmt)
        stale_people = result.scalars().all()

        # Queue refresh tasks
        refreshed_count = 0
        for person in stale_people:
            save_person_full.delay(person.tvdb_id)
            refreshed_count += 1

        return {
            "status": "success",
            "refreshed_count": refreshed_count,
            "message": f"Queued {refreshed_count} people for refresh"
        }


@celery_app.task
def cleanup_old_sync_logs():
    """
    Delete sync logs older than 30 days.

    This runs monthly (1st of month, 4 AM) to prevent log table bloat.
    """
    import asyncio
    return asyncio.run(_cleanup_old_sync_logs_async())


async def _cleanup_old_sync_logs_async():
    """Async implementation of cleanup_old_sync_logs."""
    async with AsyncSessionLocal() as db:
        threshold = datetime.utcnow() - timedelta(days=30)

        # Delete old logs
        stmt = delete(SyncLog).where(SyncLog.synced_at < threshold)
        result = await db.execute(stmt)
        await db.commit()

        return {
            "status": "success",
            "deleted_count": result.rowcount,
            "message": f"Deleted {result.rowcount} old sync logs"
        }
