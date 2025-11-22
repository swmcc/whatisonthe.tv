#!/usr/bin/env python3
"""
Remove duplicate check-ins script.

This script:
1. Finds duplicate check-ins (same user, content, episode, watched_at date)
2. Keeps the oldest check-in (lowest ID)
3. Deletes the duplicates
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.db.database import get_db
from app.models.checkin import Checkin
from app.models.user import User


async def remove_duplicate_checkins():
    """Find and remove duplicate check-ins."""
    async for db in get_db():
        print("=" * 60)
        print("Duplicate Check-in Removal Script")
        print("=" * 60)
        print()

        # Get all check-ins ordered by user, content, episode, watched_at date
        stmt = (
            select(Checkin)
            .options(selectinload(Checkin.content), selectinload(Checkin.episode))
            .order_by(Checkin.user_id, Checkin.content_id, Checkin.episode_id, Checkin.watched_at, Checkin.id)
        )
        result = await db.execute(stmt)
        all_checkins = result.scalars().all()

        print(f"📊 Found {len(all_checkins)} total check-ins")
        print()

        # Group by (user_id, content_id, episode_id, watched_at date)
        groups = {}
        for checkin in all_checkins:
            # Use date only (ignore time) for grouping
            date_key = checkin.watched_at.date() if checkin.watched_at else None
            key = (
                checkin.user_id,
                checkin.content_id,
                checkin.episode_id,  # None for movies
                date_key
            )

            if key not in groups:
                groups[key] = []
            groups[key].append(checkin)

        # Find duplicates
        duplicates_found = 0
        total_deleted = 0

        for key, checkins_group in groups.items():
            if len(checkins_group) <= 1:
                continue  # No duplicates

            user_id, content_id, episode_id, date_key = key

            # Keep the oldest (first by ID)
            keep_checkin = checkins_group[0]
            duplicate_checkins = checkins_group[1:]

            duplicates_found += 1

            content_name = keep_checkin.content.name if keep_checkin.content else "Unknown"
            episode_info = ""
            if keep_checkin.episode:
                episode_info = f" S{keep_checkin.episode.season_number}E{keep_checkin.episode.episode_number}"

            print(f"🔍 Found {len(duplicate_checkins)} duplicate(s) for:")
            print(f"   {content_name}{episode_info} on {date_key}")
            print(f"   Keeping: Check-in ID {keep_checkin.id} (created {keep_checkin.created_at})")

            # Delete duplicates
            for dup_checkin in duplicate_checkins:
                print(f"   ✗ Deleting: Check-in ID {dup_checkin.id} (created {dup_checkin.created_at})")
                await db.delete(dup_checkin)
                total_deleted += 1

            print()

        # Commit all deletions
        await db.commit()

        print("=" * 60)
        print("✅ Cleanup Complete!")
        print("=" * 60)
        print(f"  Duplicate groups found: {duplicates_found}")
        print(f"  Check-ins deleted: {total_deleted}")
        print(f"  Check-ins remaining: {len(all_checkins) - total_deleted}")


async def main():
    """Main entry point."""
    await remove_duplicate_checkins()


if __name__ == "__main__":
    asyncio.run(main())
