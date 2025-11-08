"""Content repository for DB-first lookup with async caching."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import Content
from app.models.person import Person
from app.models.credit import Credit
from app.services.tvdb import tvdb_service
from app.tasks.content import save_series_full, save_movie_full
from app.tasks.person import save_person_full


class ContentRepository:
    """Repository for content with DB-first caching strategy."""

    def __init__(self, db: AsyncSession, sync_threshold_days: int = 7):
        """
        Initialize repository.

        Args:
            db: Database session
            sync_threshold_days: Days before content is considered stale
        """
        self.db = db
        self.sync_threshold_days = sync_threshold_days

    async def get_series(self, tvdb_id: int, background_sync: bool = True) -> dict[str, Any] | None:
        """
        Get series - DB first, API fallback, async cache.

        Flow:
        1. Check DB
        2. If found and fresh → return from DB
        3. If not found or stale → get from API
        4. Queue background task to save to DB
        5. Return API data immediately

        Args:
            tvdb_id: TVDB series ID
            background_sync: Whether to queue background sync task

        Returns:
            Series data dict or None
        """
        # Step 1: Check DB
        stmt = (
            select(Content)
            .where(Content.tvdb_id == tvdb_id, Content.content_type == "series")
            .options(
                selectinload(Content.credits).selectinload(Credit.person),
                selectinload(Content.genres),
                selectinload(Content.series_detail),
                selectinload(Content.aliases),
            )
        )
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()

        # Step 2: If found and fresh, return from DB
        if content and self._is_fresh(content):
            return self._content_to_dict(content)

        # Step 3: Not found or stale - get from API
        api_data = tvdb_service.get_series_details(tvdb_id)
        if not api_data:
            return None

        # Step 4: Queue background sync (fire and forget)
        if background_sync:
            save_series_full.delay(tvdb_id, api_data)

        # Step 5: Return API data immediately (fast response!)
        return api_data

    async def get_movie(self, tvdb_id: int, background_sync: bool = True) -> dict[str, Any] | None:
        """Get movie - DB first, API fallback, async cache."""
        # Check DB
        stmt = (
            select(Content)
            .where(Content.tvdb_id == tvdb_id, Content.content_type == "movie")
            .options(
                selectinload(Content.credits).selectinload(Credit.person),
                selectinload(Content.genres),
                selectinload(Content.movie_detail),
                selectinload(Content.aliases),
            )
        )
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()

        # If found and fresh, return from DB
        if content and self._is_fresh(content):
            return self._content_to_dict(content)

        # Not found or stale - get from API
        api_data = tvdb_service.get_movie_details(tvdb_id)
        if not api_data:
            return None

        # Queue background sync
        if background_sync:
            save_movie_full.delay(tvdb_id, api_data)

        # Return API data immediately
        return api_data

    async def get_person(self, tvdb_id: int, background_sync: bool = True) -> dict[str, Any] | None:
        """Get person - DB first, API fallback, async cache."""
        # Check DB
        stmt = (
            select(Person)
            .where(Person.tvdb_id == tvdb_id)
            .options(
                selectinload(Person.credits).selectinload(Credit.content),
                selectinload(Person.aliases)
            )
        )
        result = await self.db.execute(stmt)
        person = result.scalar_one_or_none()

        # If found and fresh, return from DB
        if person and self._is_person_fresh(person):
            return self._person_to_dict(person)

        # Not found or stale - get from API
        api_data = tvdb_service.get_person_details(tvdb_id)
        if not api_data:
            return None

        # Queue background sync
        if background_sync:
            save_person_full.delay(tvdb_id, api_data)

        # Return API data immediately
        return api_data

    async def search(self, query: str, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        """
        Search for content with pagination support.

        Note: Search always hits API for freshness.
        Results are NOT auto-cached (to avoid DB bloat).
        Only save to DB when user views the detail page.

        Args:
            query: Search query
            limit: Max results per page
            offset: Starting position for pagination

        Returns:
            List of search results
        """
        # For now, just search API
        # Could add DB search for already-cached content as optimization
        return tvdb_service.search(query, limit, offset)

    def _is_fresh(self, content: Content) -> bool:
        """Check if content is fresh enough."""
        if not content.last_synced_at:
            return False

        threshold = datetime.now(timezone.utc) - timedelta(days=self.sync_threshold_days)
        return content.last_synced_at > threshold

    def _is_person_fresh(self, person: Person) -> bool:
        """Check if person is fresh enough."""
        if not person.last_synced_at:
            return False

        # People can be stale for longer (14 days)
        threshold = datetime.now(timezone.utc) - timedelta(days=14)
        return person.last_synced_at > threshold

    def _content_to_dict(self, content: Content) -> dict[str, Any]:
        """Convert Content model to API-compatible dict."""
        # Return in same format as TVDB API
        result = {
            "id": content.tvdb_id,
            "tvdb_id": content.tvdb_id,
            "name": content.name,
            "overview": content.overview,
            "year": content.year,
            "status": content.status,
            "image": content.image_url,
            "originalLanguage": content.original_language,
            "originalCountry": content.original_country,
            "genres": [{"id": g.tvdb_id, "name": g.name} for g in content.genres],
            "characters": [
                {
                    "peopleId": c.person.tvdb_id,
                    "peopleType": c.role_type.replace("_", " ").title(),
                    "personName": c.person.full_name,
                    "name": c.character_name,
                    "sort": c.sort_order,
                    "image": c.person.image_url,
                }
                for c in content.credits
            ],
        }

        # Add type-specific fields
        if content.is_series and content.series_detail:
            result["numberOfSeasons"] = content.series_detail.number_of_seasons
            result["numberOfEpisodes"] = content.series_detail.number_of_episodes
            result["averageRuntime"] = content.series_detail.average_runtime

        if content.is_movie and content.movie_detail:
            result["runtime"] = content.movie_detail.runtime

        # Include extra metadata if available
        if content.extra_metadata:
            result.update(content.extra_metadata)

        return result

    def _person_to_dict(self, person: Person) -> dict[str, Any]:
        """Convert Person model to API-compatible dict."""
        result = {
            "id": person.tvdb_id,
            "tvdb_id": person.tvdb_id,
            "name": person.full_name,
            "biography": person.biography,
            "image": person.image_url,
            "aliases": [
                {"name": a.name, "language": a.language}
                for a in person.aliases
            ],
            "characters": [
                {
                    "seriesId": c.content.tvdb_id if c.content.is_series else None,
                    "movieId": c.content.tvdb_id if c.content.is_movie else None,
                    "series": {
                        "name": c.content.name,
                        "image": c.content.image_url,
                        "year": c.content.year,
                    } if c.content.is_series else None,
                    "movie": {
                        "name": c.content.name,
                        "image": c.content.image_url,
                        "year": c.content.year,
                    } if c.content.is_movie else None,
                    "name": c.character_name,
                    "peopleType": c.role_type.replace("_", " ").title(),
                }
                for c in person.credits
            ],
        }

        # Include extra metadata if available
        if person.extra_metadata:
            result.update(person.extra_metadata)

        return result
