"""Celery tasks for content (series and movies) synchronization."""

import random
import time
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.database import SyncSessionLocal
from app.models.content import Content
from app.models.series_detail import SeriesDetail
from app.models.movie_detail import MovieDetail
from app.models.genre import Genre
from app.models.credit import Credit
from app.models.person import Person
from app.models.alias import Alias
from app.models.sync_log import SyncLog
from app.models.season import Season
from app.models.episode import Episode
from app.services.tvdb import tvdb_service
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def save_series_full(self, tvdb_id: int, api_data: dict[str, Any] | None = None):
    """
    Save complete series data to database.

    Args:
        tvdb_id: TVDB series ID
        api_data: Optional pre-fetched API data (to avoid extra API call)
    """
    # Add random delay (jitter) to spread out API calls: 5-15 seconds
    # This is background processing, so no rush - better to be nice to the API
    jitter = random.uniform(5, 15)
    time.sleep(jitter)

    start_time = datetime.utcnow()

    with SyncSessionLocal() as db:
        try:
            # Fetch from API if not provided
            if not api_data:
                api_data = tvdb_service.get_series_details(tvdb_id)

            if not api_data:
                _log_sync_failure(db, "content", tvdb_id, "Series not found in TVDB API")
                return {"status": "failed", "error": "Series not found"}

            # Check if content already exists
            stmt = select(Content).where(Content.tvdb_id == tvdb_id, Content.content_type == "series")
            result = db.execute(stmt)
            content = result.scalar_one_or_none()

            if content:
                # Update existing
                content = _update_series(db, content, api_data)
            else:
                # Create new
                content = _create_series(db, tvdb_id, api_data)

            db.commit()
            db.refresh(content)

            # Save related data (genres, credits, aliases)
            _save_genres(db, content, api_data.get("genres", []))
            _save_credits(db, content, api_data.get("characters", []))
            _save_aliases(db, content.id, "content", api_data.get("aliases", []))

            # Save seasons and episodes for series
            _save_seasons_and_episodes(db, content, tvdb_id, api_data)

            db.commit()

            # Log success
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            _log_sync_success(db, "content", content.id, tvdb_id, duration_ms)
            db.commit()

            return {"status": "success", "content_id": content.id}

        except Exception as e:
            db.rollback()
            _log_sync_failure(db, "content", tvdb_id, str(e))
            db.commit()
            raise


@celery_app.task(bind=True, max_retries=3)
def save_movie_full(self, tvdb_id: int, api_data: dict[str, Any] | None = None):
    """
    Save complete movie data to database.

    Args:
        tvdb_id: TVDB movie ID
        api_data: Optional pre-fetched API data
    """
    # Add random delay (jitter) to spread out API calls: 5-15 seconds
    # This is background processing, so no rush - better to be nice to the API
    jitter = random.uniform(5, 15)
    time.sleep(jitter)

    start_time = datetime.utcnow()

    with SyncSessionLocal() as db:
        try:
            # Fetch from API if not provided
            if not api_data:
                api_data = tvdb_service.get_movie_details(tvdb_id)

            if not api_data:
                _log_sync_failure(db, "content", tvdb_id, "Movie not found in TVDB API")
                return {"status": "failed", "error": "Movie not found"}

            # Check if content already exists
            stmt = select(Content).where(Content.tvdb_id == tvdb_id, Content.content_type == "movie")
            result = db.execute(stmt)
            content = result.scalar_one_or_none()

            if content:
                # Update existing
                content = _update_movie(db, content, api_data)
            else:
                # Create new
                content = _create_movie(db, tvdb_id, api_data)

            db.commit()
            db.refresh(content)

            # Save related data
            _save_genres(db, content, api_data.get("genres", []))
            _save_credits(db, content, api_data.get("characters", []))
            _save_aliases(db, content.id, "content", api_data.get("aliases", []))

            db.commit()

            # Log success
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            _log_sync_success(db, "content", content.id, tvdb_id, duration_ms)
            db.commit()

            return {"status": "success", "content_id": content.id}

        except Exception as e:
            db.rollback()
            _log_sync_failure(db, "content", tvdb_id, str(e))
            db.commit()
            raise


# Helper functions

def _create_series(db, tvdb_id: int, api_data: dict) -> Content:
    """Create new series content."""
    content = Content(
        tvdb_id=tvdb_id,
        content_type="series",
        name=api_data.get("name"),
        overview=api_data.get("overview"),
        year=api_data.get("year"),
        status=api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status"),
        image_url=api_data.get("image"),
        original_language=api_data.get("originalLanguage"),
        original_country=api_data.get("originalCountry"),
        last_synced_at=datetime.utcnow(),
        extra_metadata=api_data
    )
    db.add(content)
    db.flush()

    # Add series details
    series_detail = SeriesDetail(
        content_id=content.id,
        number_of_seasons=api_data.get("numberOfSeasons"),
        number_of_episodes=api_data.get("numberOfEpisodes"),
        average_runtime=api_data.get("averageRuntime"),
    )
    db.add(series_detail)

    return content


def _update_series(db, content: Content, api_data: dict) -> Content:
    """Update existing series content."""
    content.name = api_data.get("name")
    content.overview = api_data.get("overview")
    content.year = api_data.get("year")
    content.status = api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status")
    content.image_url = api_data.get("image")
    content.last_synced_at = datetime.utcnow()
    content.extra_metadata = api_data

    # Update series details
    if content.series_detail:
        content.series_detail.number_of_seasons = api_data.get("numberOfSeasons")
        content.series_detail.number_of_episodes = api_data.get("numberOfEpisodes")
        content.series_detail.average_runtime = api_data.get("averageRuntime")

    return content


def _create_movie(db, tvdb_id: int, api_data: dict) -> Content:
    """Create new movie content."""
    content = Content(
        tvdb_id=tvdb_id,
        content_type="movie",
        name=api_data.get("name"),
        overview=api_data.get("overview"),
        year=api_data.get("year"),
        status=api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status"),
        image_url=api_data.get("image"),
        original_language=api_data.get("originalLanguage"),
        original_country=api_data.get("originalCountry"),
        last_synced_at=datetime.utcnow(),
        extra_metadata=api_data
    )
    db.add(content)
    db.flush()

    # Add movie details
    movie_detail = MovieDetail(
        content_id=content.id,
        runtime=api_data.get("runtime"),
    )
    db.add(movie_detail)

    return content


def _update_movie(db, content: Content, api_data: dict) -> Content:
    """Update existing movie content."""
    content.name = api_data.get("name")
    content.overview = api_data.get("overview")
    content.year = api_data.get("year")
    content.status = api_data.get("status", {}).get("name") if isinstance(api_data.get("status"), dict) else api_data.get("status")
    content.image_url = api_data.get("image")
    content.last_synced_at = datetime.utcnow()
    content.extra_metadata = api_data

    # Update movie details
    if content.movie_detail:
        content.movie_detail.runtime = api_data.get("runtime")

    return content


def _save_genres(db, content: Content, genres_data: list):
    """Save genres for content."""
    # Clear existing genre associations
    content.genres.clear()

    if not genres_data:
        return

    for genre_data in genres_data:
        genre_name = genre_data.get("name")
        if not genre_name:
            continue

        # Get or create genre
        stmt = select(Genre).where(Genre.name == genre_name)
        result = db.execute(stmt)
        genre = result.scalar_one_or_none()

        if not genre:
            genre = Genre(
                tvdb_id=genre_data.get("id"),
                name=genre_name,
                slug=genre_name.lower().replace(" ", "-")
            )
            db.add(genre)
            db.flush()

        # Add to content (no need to check, we cleared above)
        content.genres.append(genre)


def _save_credits(db, content: Content, characters_data: list):
    """Save credits (cast and crew) for content."""
    if not characters_data:
        return

    # Clear existing credits
    stmt = select(Credit).where(Credit.content_id == content.id)
    result = db.execute(stmt)
    existing_credits = result.scalars().all()
    for credit in existing_credits:
        db.delete(credit)

    # Flush deletes to avoid unique constraint violations
    db.flush()

    for char_data in characters_data:
        person_id = char_data.get("peopleId")
        if not person_id:
            continue

        # Get or create person (minimal data, full sync happens in person tasks)
        stmt = select(Person).where(Person.tvdb_id == person_id)
        result = db.execute(stmt)
        person = result.scalar_one_or_none()

        if not person:
            person_name = char_data.get("personName", "Unknown")
            # Parse name into first/last
            name_parts = person_name.rsplit(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            person = Person(
                tvdb_id=person_id,
                full_name=person_name,
                first_name=first_name,
                last_name=last_name,
                last_synced_at=None  # Mark as needing sync
            )
            db.add(person)
            db.flush()

        # Create credit
        role_type_map = {
            "Actor": "actor",
            "Director": "director",
            "Writer": "writer",
            "Producer": "producer",
            "Executive Producer": "executive_producer",
        }
        role_type = role_type_map.get(char_data.get("peopleType"), "crew")

        credit = Credit(
            content_id=content.id,
            person_id=person.id,
            role_type=role_type,
            character_name=char_data.get("name") if role_type == "actor" else None,
            sort_order=char_data.get("sort", 999)
        )
        db.add(credit)


def _save_aliases(db, entity_id: int, entity_type: str, aliases_data: list):
    """Save aliases for content or person."""
    if not aliases_data:
        return

    # Clear existing aliases
    stmt = select(Alias).where(
        Alias.entity_type == entity_type,
        Alias.entity_id == entity_id
    )
    result = db.execute(stmt)
    existing_aliases = result.scalars().all()
    for alias in existing_aliases:
        db.delete(alias)

    # Flush deletes to avoid potential duplicates
    db.flush()

    for alias_data in aliases_data:
        alias_name = alias_data.get("name")
        alias_lang = alias_data.get("language", "eng")

        if not alias_name:
            continue

        alias = Alias(
            entity_type=entity_type,
            entity_id=entity_id,
            name=alias_name,
            language=alias_lang
        )
        db.add(alias)


def _save_seasons_and_episodes(db, content: Content, tvdb_id: int, api_data: dict):
    """Save seasons and episodes for a series."""
    # Get seasons data from API response
    seasons_data = api_data.get("seasons", [])

    if not seasons_data:
        return

    # Clear existing episodes first (to avoid foreign key issues)
    stmt = select(Episode).where(Episode.content_id == content.id)
    result = db.execute(stmt)
    existing_episodes = result.scalars().all()
    for episode in existing_episodes:
        db.delete(episode)

    # Clear existing seasons
    stmt = select(Season).where(Season.content_id == content.id)
    result = db.execute(stmt)
    existing_seasons = result.scalars().all()
    for season in existing_seasons:
        db.delete(season)

    # Flush deletes to avoid constraint violations
    db.flush()

    # Process each season
    for season_data in seasons_data:
        season_tvdb_id = season_data.get("id")
        if not season_tvdb_id:
            continue

        season_number = season_data.get("number", 0)
        season_type = season_data.get("type", {})

        # Create new season
        season = Season(
            tvdb_id=season_tvdb_id,
            content_id=content.id,
            season_number=season_number,
            name=season_data.get("name"),
            overview=season_data.get("overview"),
            image_url=season_data.get("image"),
            season_type=season_type.get("name") if isinstance(season_type, dict) else None,
            season_type_id=season_type.get("id") if isinstance(season_type, dict) else None,
            year=season_data.get("year"),
            last_synced_at=datetime.utcnow(),
            extra_metadata=season_data
        )
        db.add(season)

    db.flush()

    # Now fetch and save episodes
    episodes_response = tvdb_service.get_series_episodes(tvdb_id)
    if not episodes_response:
        return

    episodes_data = episodes_response.get("episodes", [])
    if not episodes_data:
        return

    # Get season mapping (for linking episodes to seasons)
    stmt = select(Season).where(Season.content_id == content.id)
    result = db.execute(stmt)
    seasons_by_number = {s.season_number: s for s in result.scalars().all()}

    # Process each episode
    for episode_data in episodes_data:
        episode_tvdb_id = episode_data.get("id")
        if not episode_tvdb_id:
            continue

        season_number = episode_data.get("seasonNumber", 0)
        episode_number = episode_data.get("number", 0)

        # Find matching season
        season = seasons_by_number.get(season_number)

        # Parse aired date
        aired_str = episode_data.get("aired")
        aired_date = None
        if aired_str:
            try:
                from datetime import datetime as dt
                aired_date = dt.strptime(aired_str, "%Y-%m-%d").date()
            except:
                pass

        # Create new episode
        episode = Episode(
            tvdb_id=episode_tvdb_id,
            content_id=content.id,
            season_id=season.id if season else None,
            season_number=season_number,
            episode_number=episode_number,
            absolute_number=episode_data.get("absoluteNumber"),
            name=episode_data.get("name"),
            overview=episode_data.get("overview"),
            image_url=episode_data.get("image"),
            aired=aired_date,
            runtime=episode_data.get("runtime"),
            year=episode_data.get("year"),
            is_movie=episode_data.get("isMovie", 0),
            finale_type=episode_data.get("finaleType"),
            airs_before_season=episode_data.get("airsBeforeSeason"),
            airs_before_episode=episode_data.get("airsBeforeEpisode"),
            airs_after_season=episode_data.get("airsAfterSeason"),
            last_synced_at=datetime.utcnow(),
            extra_metadata=episode_data
        )
        db.add(episode)


def _log_sync_success(db, entity_type: str, entity_id: int, tvdb_id: int, duration_ms: int):
    """Log successful sync."""
    log = SyncLog(
        entity_type=entity_type,
        entity_id=entity_id,
        tvdb_id=tvdb_id,
        sync_status="success",
        sync_type="full",
        duration_ms=duration_ms
    )
    db.add(log)


def _log_sync_failure(db, entity_type: str, tvdb_id: int, error_message: str):
    """Log failed sync."""
    log = SyncLog(
        entity_type=entity_type,
        tvdb_id=tvdb_id,
        sync_status="failed",
        sync_type="full",
        error_message=error_message
    )
    db.add(log)
