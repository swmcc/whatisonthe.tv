#!/usr/bin/env python3
"""Clean up duplicate seasons and episodes, and reset checkins."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select, func, delete
from app.db.database import get_db
from app.models.season import Season
from app.models.episode import Episode
from app.models.checkin import Checkin


async def cleanup_duplicates():
    """Clean up duplicate seasons/episodes and delete all checkins."""
    async for db in get_db():
        print("🧹 Starting cleanup...")

        # 1. Delete all checkins
        print("\n📋 Deleting all checkins...")
        stmt = delete(Checkin)
        result = await db.execute(stmt)
        await db.commit()
        print(f"   ✓ Deleted {result.rowcount} checkins")

        # 2. Find and delete duplicate episodes
        print("\n🎬 Finding duplicate episodes...")
        # Get all episodes grouped by tvdb_id
        stmt = select(
            Episode.tvdb_id,
            func.count(Episode.id).label('count'),
            func.min(Episode.id).label('keep_id')
        ).group_by(Episode.tvdb_id).having(func.count(Episode.id) > 1)

        result = await db.execute(stmt)
        duplicate_episodes = result.all()

        if duplicate_episodes:
            print(f"   Found {len(duplicate_episodes)} sets of duplicate episodes")
            total_deleted = 0
            for dup in duplicate_episodes:
                # Delete all except the first one (with minimum id)
                stmt = delete(Episode).where(
                    Episode.tvdb_id == dup.tvdb_id,
                    Episode.id != dup.keep_id
                )
                result = await db.execute(stmt)
                deleted = result.rowcount
                total_deleted += deleted
                print(f"   ✓ Deleted {deleted} duplicate(s) of episode tvdb_id={dup.tvdb_id}")

            await db.commit()
            print(f"   ✓ Total episodes deleted: {total_deleted}")
        else:
            print("   ✓ No duplicate episodes found")

        # 3. Find and delete duplicate seasons (by content_id + season_number)
        print("\n📺 Finding duplicate seasons...")
        stmt = select(
            Season.content_id,
            Season.season_number,
            func.count(Season.id).label('count'),
            func.min(Season.id).label('keep_id')
        ).group_by(Season.content_id, Season.season_number).having(func.count(Season.id) > 1)

        result = await db.execute(stmt)
        duplicate_seasons = result.all()

        if duplicate_seasons:
            print(f"   Found {len(duplicate_seasons)} sets of duplicate seasons")
            total_deleted = 0
            for dup in duplicate_seasons:
                # Delete all except the first one (with minimum id)
                stmt = delete(Season).where(
                    Season.content_id == dup.content_id,
                    Season.season_number == dup.season_number,
                    Season.id != dup.keep_id
                )
                result = await db.execute(stmt)
                deleted = result.rowcount
                total_deleted += deleted
                print(f"   ✓ Deleted {deleted} duplicate(s) of season {dup.season_number} for content {dup.content_id}")

            await db.commit()
            print(f"   ✓ Total seasons deleted: {total_deleted}")
        else:
            print("   ✓ No duplicate seasons found")

        print("\n✨ Cleanup complete!")
        break


if __name__ == "__main__":
    print("=" * 60)
    print("CLEANUP: Removing duplicates and resetting checkins")
    print("=" * 60)
    asyncio.run(cleanup_duplicates())
