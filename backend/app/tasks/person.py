"""Celery tasks for person synchronization."""

from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.person import Person
from app.models.sync_log import SyncLog
from app.services.tvdb import tvdb_service
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def save_person_full(self, tvdb_id: int, api_data: dict[str, Any] | None = None):
    """
    Save complete person data to database.

    Args:
        tvdb_id: TVDB person ID
        api_data: Optional pre-fetched API data
    """
    import asyncio
    return asyncio.run(_save_person_full_async(tvdb_id, api_data))


async def _save_person_full_async(tvdb_id: int, api_data: dict[str, Any] | None = None):
    """Async implementation of save_person_full."""
    start_time = datetime.utcnow()

    async with AsyncSessionLocal() as db:
        try:
            # Fetch from API if not provided
            if not api_data:
                api_data = tvdb_service.get_person_details(tvdb_id)

            if not api_data:
                await _log_sync_failure(db, tvdb_id, "Person not found in TVDB API")
                return {"status": "failed", "error": "Person not found"}

            # Check if person already exists
            stmt = select(Person).where(Person.tvdb_id == tvdb_id)
            result = await db.execute(stmt)
            person = result.scalar_one_or_none()

            # Parse name
            full_name = api_data.get("name", "Unknown")
            name_parts = full_name.rsplit(" ", 1)  # Split from right to handle "First Middle Last"
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            if person:
                # Update existing
                person.full_name = full_name
                person.first_name = first_name
                person.last_name = last_name
                person.biography = api_data.get("biography")
                person.image_url = api_data.get("image")
                person.last_synced_at = datetime.utcnow()
                person.extra_metadata = api_data
            else:
                # Create new
                person = Person(
                    tvdb_id=tvdb_id,
                    full_name=full_name,
                    first_name=first_name,
                    last_name=last_name,
                    biography=api_data.get("biography"),
                    image_url=api_data.get("image"),
                    last_synced_at=datetime.utcnow(),
                    extra_metadata=api_data
                )
                db.add(person)

            await db.commit()
            await db.refresh(person)

            # Log success
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await _log_sync_success(db, person.id, tvdb_id, duration_ms)
            await db.commit()

            return {"status": "success", "person_id": person.id}

        except Exception as e:
            await db.rollback()
            await _log_sync_failure(db, tvdb_id, str(e))
            await db.commit()
            raise


async def _log_sync_success(db, person_id: int, tvdb_id: int, duration_ms: int):
    """Log successful sync."""
    log = SyncLog(
        entity_type="person",
        entity_id=person_id,
        tvdb_id=tvdb_id,
        sync_status="success",
        sync_type="full",
        duration_ms=duration_ms
    )
    db.add(log)


async def _log_sync_failure(db, tvdb_id: int, error_message: str):
    """Log failed sync."""
    log = SyncLog(
        entity_type="person",
        tvdb_id=tvdb_id,
        sync_status="failed",
        sync_type="full",
        error_message=error_message
    )
    db.add(log)
