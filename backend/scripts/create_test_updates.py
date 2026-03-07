#!/usr/bin/env python3
"""Script to create test watchlist updates for development."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

# Add the app to path
sys.path.insert(0, "/Users/swm/Code/whatisonthe.tv/backend")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from app.core.config import settings
from app.models import User, WatchlistItem
from app.models.watchlist_update import WatchlistUpdate, UpdateType


async def create_test_updates():
    """Create test watchlist updates."""
    # Create async engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get the first user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if not user:
            print("No users found. Please create a user first.")
            return

        print(f"Creating test updates for user: {user.email}")

        # Get user's watchlist items with relationships loaded
        result = await db.execute(
            select(WatchlistItem)
            .where(WatchlistItem.user_id == user.id)
            .options(selectinload(WatchlistItem.content), selectinload(WatchlistItem.person))
            .limit(10)
        )
        watchlist_items = result.scalars().all()

        if not watchlist_items:
            print("No watchlist items found. Please add items to watchlist first.")
            return

        # Create test updates for each watchlist item
        test_updates = []
        now = datetime.now(timezone.utc)

        for i, item in enumerate(watchlist_items):
            if item.content:
                content_name = item.content.name

                # New season announcement
                test_updates.append(
                    WatchlistUpdate(
                        user_id=user.id,
                        watchlist_item_id=item.id,
                        update_type=UpdateType.NEW_EPISODE,
                        description=f"{content_name} - Season 6 has been announced!",
                        details={
                            "season_number": 6,
                            "season_name": "Season 6",
                            "type": "new_season",
                        },
                        is_read=False,
                        created_at=now - timedelta(hours=i * 2),
                    )
                )

                # Episode air date confirmed
                episodes = [
                    (5, 10, "The Final Frontier", "2026-04-15"),
                    (5, 11, "New Horizons", "2026-04-22"),
                    (5, 12, "The Long Goodbye", "2026-04-29"),
                    (6, 1, "Premiere", "2026-09-10"),
                ]
                for ep_idx, (season, ep, name, date) in enumerate(episodes):
                    test_updates.append(
                        WatchlistUpdate(
                            user_id=user.id,
                            watchlist_item_id=item.id,
                            update_type=UpdateType.NEW_EPISODE,
                            description=f'{content_name} S{season:02d}E{ep:02d} "{name}" airs {date}',
                            details={
                                "season_number": season,
                                "episode_number": ep,
                                "episode_name": name,
                                "air_date": date,
                                "type": "episode_dated",
                            },
                            is_read=False,
                            created_at=now - timedelta(hours=i * 3 + ep_idx + 1),
                        )
                    )

                # Status change
                test_updates.append(
                    WatchlistUpdate(
                        user_id=user.id,
                        watchlist_item_id=item.id,
                        update_type=UpdateType.STATUS_CHANGE,
                        description=f"{content_name} status changed from 'Continuing' to 'Renewed'",
                        details={
                            "old_status": "Continuing",
                            "new_status": "Renewed",
                        },
                        is_read=False,
                        created_at=now - timedelta(days=1),
                    )
                )

            elif item.person:
                person_name = item.person.full_name
                role_filter = item.person_role_filter

                # Multiple projects per person for more test data
                if role_filter == "director":
                    projects = [
                        ("Code Zero", "Director", "directing"),
                        ("The Midnight Sun", "Director", "directing"),
                        ("Echoes of Tomorrow", "Executive Producer", "executive producing"),
                    ]
                elif role_filter == "actor":
                    projects = [
                        ("The Last Horizon", "Lead Role", "cast in"),
                        ("Midnight in Berlin", "Guest Star", "guest starring in"),
                        ("The Crown Season 8", "Recurring Role", "cast in"),
                        ("Untitled Marvel Project", "Supporting Role", "cast in"),
                    ]
                else:
                    # Default - mix of roles
                    projects = [
                        ("The Last Horizon", "Lead Role", "cast in"),
                        ("The Silent Storm", "Director", "directing"),
                        ("Neon Nights", "Guest Star", "guest starring in"),
                        ("Project Aurora", "Executive Producer", "executive producing"),
                    ]

                for proj_idx, (project_name, role, verb) in enumerate(projects):
                    if verb == "directing":
                        description = f'{person_name} is directing "{project_name}"'
                    elif verb == "executive producing":
                        description = f'{person_name} is executive producing "{project_name}"'
                    elif verb == "guest starring in":
                        description = f'{person_name} guest starring in "{project_name}"'
                    else:
                        description = f'{person_name} cast in "{project_name}" as {role}'

                    test_updates.append(
                        WatchlistUpdate(
                            user_id=user.id,
                            watchlist_item_id=item.id,
                            update_type=UpdateType.NEW_CAST,
                            description=description,
                            details={
                                "project_name": project_name,
                                "role": role,
                            },
                            is_read=False,
                            created_at=now - timedelta(hours=i * 4 + proj_idx * 2),
                        )
                    )

        # Clear existing test updates first
        result = await db.execute(
            select(WatchlistUpdate).where(WatchlistUpdate.user_id == user.id)
        )
        existing = result.scalars().all()
        for update in existing:
            await db.delete(update)

        # Add new test updates
        for update in test_updates:
            db.add(update)

        await db.commit()
        print(f"Created {len(test_updates)} test updates!")
        print("\nUpdates created:")
        for u in test_updates:
            status = "unread" if not u.is_read else "read"
            print(f"  - [{status}] {u.update_type.value}: {u.description[:60]}...")


if __name__ == "__main__":
    asyncio.run(create_test_updates())
