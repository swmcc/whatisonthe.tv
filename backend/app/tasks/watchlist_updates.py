"""Celery tasks for detecting watchlist updates."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import SyncSessionLocal
from app.models import Content, WatchlistItem, Season, Episode
from app.models.watchlist_update import WatchlistUpdate, UpdateType
from app.services.tvdb import tvdb_service
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def check_watchlist_updates(self):
    """
    Check for updates to content on users' watchlists.

    Detects:
    - New seasons added to shows
    - Episodes that now have air dates (were TBD)
    - Status changes (renewed, cancelled, ended)

    This task should run daily via Celery beat.
    """
    with SyncSessionLocal() as db:
        # Get all unique content IDs from all watchlists
        stmt = (
            select(WatchlistItem)
            .where(WatchlistItem.content_id.isnot(None))
            .options(selectinload(WatchlistItem.content))
        )
        result = db.execute(stmt)
        watchlist_items = result.scalars().all()

        # Group by content to avoid duplicate API calls
        content_to_users: dict[int, list[WatchlistItem]] = {}
        for item in watchlist_items:
            if item.content_id not in content_to_users:
                content_to_users[item.content_id] = []
            content_to_users[item.content_id].append(item)

        updates_created = 0

        for content_id, items in content_to_users.items():
            content = items[0].content
            if not content or content.content_type != "series":
                continue

            try:
                updates = _check_content_for_updates(db, content, items)
                updates_created += updates
            except Exception as e:
                print(f"Error checking content {content_id}: {e}")
                continue

        db.commit()
        return {"status": "success", "updates_created": updates_created}


def _check_content_for_updates(db, content: Content, watchlist_items: list[WatchlistItem]) -> int:
    """
    Check a single content item for updates.

    Returns number of updates created.
    """
    updates_created = 0

    # Get current seasons from database
    stmt = select(Season).where(Season.content_id == content.id)
    result = db.execute(stmt)
    existing_seasons = {s.season_number: s for s in result.scalars().all()}

    # Get current episodes from database
    stmt = select(Episode).where(Episode.content_id == content.id)
    result = db.execute(stmt)
    existing_episodes = {(e.season_number, e.episode_number): e for e in result.scalars().all()}

    # Fetch latest from TVDB
    api_data = tvdb_service.get_series_details(content.tvdb_id)
    if not api_data:
        return 0

    # Check for status changes
    new_status = api_data.get("status", {})
    if isinstance(new_status, dict):
        new_status = new_status.get("name")

    if new_status and content.status and new_status != content.status:
        updates_created += _create_status_update(
            db, content, watchlist_items, content.status, new_status
        )

    # Check for new seasons
    api_seasons = api_data.get("seasons", [])
    for season_data in api_seasons:
        season_number = season_data.get("number", 0)
        season_type = season_data.get("type", {})

        # Only check "Aired Order" seasons (type_id = 1)
        season_type_id = season_type.get("id") if isinstance(season_type, dict) else None
        if season_type_id and season_type_id != 1:
            continue

        if season_number > 0 and season_number not in existing_seasons:
            updates_created += _create_new_season_update(
                db, content, watchlist_items, season_number, season_data
            )

    # Fetch episodes to check for newly dated episodes
    episodes_response = tvdb_service.get_series_episodes(content.tvdb_id)
    if episodes_response:
        api_episodes = episodes_response.get("episodes", [])

        for ep_data in api_episodes:
            season_num = ep_data.get("seasonNumber", 0)
            ep_num = ep_data.get("number", 0)
            aired_str = ep_data.get("aired")

            if season_num <= 0 or ep_num <= 0:
                continue

            ep_key = (season_num, ep_num)
            existing_ep = existing_episodes.get(ep_key)

            # Check if episode now has an air date but didn't before
            if aired_str and existing_ep and not existing_ep.aired:
                updates_created += _create_episode_dated_update(
                    db, content, watchlist_items, existing_ep, aired_str
                )

    return updates_created


def _create_status_update(
    db, content: Content, watchlist_items: list[WatchlistItem],
    old_status: str, new_status: str
) -> int:
    """Create status change updates for all users watching this content."""
    count = 0
    now = datetime.now(timezone.utc)

    for item in watchlist_items:
        update = WatchlistUpdate(
            user_id=item.user_id,
            watchlist_item_id=item.id,
            update_type=UpdateType.STATUS_CHANGE,
            description=f"{content.name} status changed from '{old_status}' to '{new_status}'",
            details={
                "old_status": old_status,
                "new_status": new_status,
            },
            is_read=False,
            created_at=now,
        )
        db.add(update)
        count += 1

    return count


def _create_new_season_update(
    db, content: Content, watchlist_items: list[WatchlistItem],
    season_number: int, season_data: dict[str, Any]
) -> int:
    """Create new season updates for all users watching this content."""
    count = 0
    now = datetime.now(timezone.utc)

    season_name = season_data.get("name", f"Season {season_number}")

    for item in watchlist_items:
        update = WatchlistUpdate(
            user_id=item.user_id,
            watchlist_item_id=item.id,
            update_type=UpdateType.NEW_EPISODE,  # Using NEW_EPISODE for seasons too
            description=f"{content.name} - {season_name} has been announced!",
            details={
                "season_number": season_number,
                "season_name": season_name,
                "type": "new_season",
            },
            is_read=False,
            created_at=now,
        )
        db.add(update)
        count += 1

    return count


def _create_episode_dated_update(
    db, content: Content, watchlist_items: list[WatchlistItem],
    episode: Episode, aired_str: str
) -> int:
    """Create updates when an episode gets a confirmed air date."""
    count = 0
    now = datetime.now(timezone.utc)

    # Parse the air date for display
    try:
        air_date = datetime.strptime(aired_str, "%Y-%m-%d").date()
        air_date_display = air_date.strftime("%B %d, %Y")
    except ValueError:
        air_date_display = aired_str

    ep_name = episode.name or f"Episode {episode.episode_number}"

    for item in watchlist_items:
        update = WatchlistUpdate(
            user_id=item.user_id,
            watchlist_item_id=item.id,
            update_type=UpdateType.NEW_EPISODE,
            description=f"{content.name} S{episode.season_number:02d}E{episode.episode_number:02d} \"{ep_name}\" airs {air_date_display}",
            details={
                "season_number": episode.season_number,
                "episode_number": episode.episode_number,
                "episode_name": ep_name,
                "air_date": aired_str,
                "type": "episode_dated",
            },
            is_read=False,
            created_at=now,
        )
        db.add(update)
        count += 1

    return count
