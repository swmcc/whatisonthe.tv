"""Celery tasks for detecting watchlist updates."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import SyncSessionLocal
from app.models import Content, WatchlistItem, Season, Episode, Person, Credit
from app.models.watchlist_update import WatchlistUpdate, UpdateType
from app.services.tvdb import tvdb_service
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def check_watchlist_updates(self):
    """
    Check for updates to content and people on users' watchlists.

    Detects:
    - New seasons added to shows
    - Episodes that now have air dates (were TBD)
    - Status changes (renewed, cancelled, ended)
    - New cast members on shows
    - New projects for people on watchlist

    This task should run daily via Celery beat.
    """
    print("=" * 60)
    print("WATCHLIST UPDATE CHECK STARTED")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    with SyncSessionLocal() as db:
        updates_created = 0

        # --- Check content (shows) on watchlists ---
        stmt = (
            select(WatchlistItem)
            .where(WatchlistItem.content_id.isnot(None))
            .options(selectinload(WatchlistItem.content))
        )
        result = db.execute(stmt)
        content_watchlist_items = result.scalars().all()

        # Group by content to avoid duplicate API calls
        content_to_users: dict[int, list[WatchlistItem]] = {}
        for item in content_watchlist_items:
            if item.content_id not in content_to_users:
                content_to_users[item.content_id] = []
            content_to_users[item.content_id].append(item)

        print(f"\n[CONTENT] Checking {len(content_to_users)} shows on watchlists...")

        for content_id, items in content_to_users.items():
            content = items[0].content
            if not content or content.content_type != "series":
                continue

            print(f"  - Checking: {content.name} (TVDB: {content.tvdb_id})")

            try:
                updates = _check_content_for_updates(db, content, items)
                if updates > 0:
                    print(f"    → Found {updates} update(s)!")
                updates_created += updates
            except Exception as e:
                print(f"    → ERROR: {e}")
                continue

        # --- Check people on watchlists ---
        stmt = (
            select(WatchlistItem)
            .where(WatchlistItem.person_id.isnot(None))
            .options(selectinload(WatchlistItem.person))
        )
        result = db.execute(stmt)
        person_watchlist_items = result.scalars().all()

        # Group by person to avoid duplicate API calls
        person_to_users: dict[int, list[WatchlistItem]] = {}
        for item in person_watchlist_items:
            if item.person_id not in person_to_users:
                person_to_users[item.person_id] = []
            person_to_users[item.person_id].append(item)

        print(f"\n[PEOPLE] Checking {len(person_to_users)} people on watchlists...")

        for person_id, items in person_to_users.items():
            person = items[0].person
            if not person:
                continue

            print(f"  - Checking: {person.full_name} (TVDB: {person.tvdb_id})")

            try:
                updates = _check_person_for_updates(db, person, items)
                if updates > 0:
                    print(f"    → Found {updates} update(s)!")
                updates_created += updates
            except Exception as e:
                print(f"    → ERROR: {e}")
                continue

        db.commit()

        print("\n" + "=" * 60)
        print("WATCHLIST UPDATE CHECK COMPLETE")
        print(f"Total updates created: {updates_created}")
        print("=" * 60)

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

    print(f"      DB: {len(existing_seasons)} seasons, {len(existing_episodes)} episodes, status='{content.status}'")

    # Fetch latest from TVDB
    api_data = tvdb_service.get_series_details(content.tvdb_id)
    if not api_data:
        print("      TVDB: No data returned!")
        return 0

    # Check for status changes
    new_status = api_data.get("status", {})
    if isinstance(new_status, dict):
        new_status = new_status.get("name")

    print(f"      TVDB: status='{new_status}'")

    if new_status and content.status and new_status != content.status:
        print(f"      → STATUS CHANGE: '{content.status}' → '{new_status}'")
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

    # Check for new cast members
    updates_created += _check_content_for_new_cast(db, content, watchlist_items, api_data)

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


def _check_person_for_updates(db, person: Person, watchlist_items: list[WatchlistItem]) -> int:
    """
    Check a person for new projects/credits.

    Returns number of updates created.
    """
    updates_created = 0

    # Get existing credits from database
    stmt = select(Credit).where(Credit.person_id == person.id)
    result = db.execute(stmt)
    existing_credits = result.scalars().all()

    # Build set of existing (content_tvdb_id, role_type) pairs
    existing_credit_keys: set[tuple[int, str]] = set()
    for credit in existing_credits:
        if credit.content and credit.content.tvdb_id:
            existing_credit_keys.add((credit.content.tvdb_id, credit.role_type))

    print(f"      DB: {len(existing_credits)} credits tracked")

    # Fetch latest from TVDB
    api_data = tvdb_service.get_person_details(person.tvdb_id)
    if not api_data:
        print("      TVDB: No data returned!")
        return 0

    now = datetime.now(timezone.utc)

    # Check characters (acting roles)
    api_characters = api_data.get("characters", [])
    print(f"      TVDB: {len(api_characters)} characters/roles")

    new_roles_found = 0
    for char in api_characters:
        series_id = char.get("seriesId")
        movie_id = char.get("movieId")
        content_tvdb_id = series_id or movie_id

        if not content_tvdb_id:
            continue

        credit_key = (content_tvdb_id, "actor")
        if credit_key not in existing_credit_keys:
            # New acting role found
            content_name = char.get("seriesName") or char.get("movieName") or char.get("name") or "Unknown Project"
            character_name = char.get("name") or char.get("personName") or ""

            new_roles_found += 1
            print(f"      → NEW ROLE: {content_name}")

            # Check role filter if set
            for item in watchlist_items:
                if item.person_role_filter and item.person_role_filter != "actor":
                    continue

                description = f'{person.full_name} cast in "{content_name}"'
                if character_name and character_name != person.full_name:
                    description += f' as {character_name}'

                update = WatchlistUpdate(
                    user_id=item.user_id,
                    watchlist_item_id=item.id,
                    update_type=UpdateType.NEW_CAST,
                    description=description,
                    details={
                        "content_tvdb_id": content_tvdb_id,
                        "content_name": content_name,
                        "role_type": "actor",
                        "character_name": character_name,
                    },
                    is_read=False,
                    created_at=now,
                )
                db.add(update)
                updates_created += 1

            # Add to set so we don't duplicate
            existing_credit_keys.add(credit_key)

    if new_roles_found == 0:
        print("      No new roles found")

    return updates_created


def _check_content_for_new_cast(
    db, content: Content, watchlist_items: list[WatchlistItem], api_data: dict[str, Any]
) -> int:
    """Check if any new cast members have been added to the content."""
    updates_created = 0

    # Get existing cast from database
    stmt = select(Credit).where(
        Credit.content_id == content.id,
        Credit.role_type == "actor"
    )
    result = db.execute(stmt)
    existing_cast = result.scalars().all()

    # Build set of existing person TVDB IDs
    existing_person_ids: set[int] = set()
    for credit in existing_cast:
        if credit.person and credit.person.tvdb_id:
            existing_person_ids.add(credit.person.tvdb_id)

    # Check characters from API
    api_characters = api_data.get("characters", [])
    now = datetime.now(timezone.utc)

    for char in api_characters:
        person_id = char.get("peopleId") or char.get("personId")
        if not person_id or person_id in existing_person_ids:
            continue

        # Only notify for main cast (low sort order)
        sort_order = char.get("sort", 999)
        if sort_order > 10:  # Only top 10 billed
            continue

        person_name = char.get("personName") or "Unknown"
        character_name = char.get("name") or ""

        for item in watchlist_items:
            description = f'{person_name} joined the cast of "{content.name}"'
            if character_name:
                description += f' as {character_name}'

            update = WatchlistUpdate(
                user_id=item.user_id,
                watchlist_item_id=item.id,
                update_type=UpdateType.NEW_CAST,
                description=description,
                details={
                    "person_tvdb_id": person_id,
                    "person_name": person_name,
                    "character_name": character_name,
                    "sort_order": sort_order,
                },
                is_read=False,
                created_at=now,
            )
            db.add(update)
            updates_created += 1

        # Add to set so we don't duplicate
        existing_person_ids.add(person_id)

    return updates_created
