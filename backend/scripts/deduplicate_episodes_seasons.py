#!/usr/bin/env python3
"""
Deduplicate episodes and seasons script.

This script:
1. Finds duplicate episodes/seasons by tvdb_id
2. Keeps the oldest record (lowest ID)
3. Updates all checkins to point to the kept record
4. Deletes the duplicate records
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
from app.models.episode import Episode
from app.models.season import Season
from app.models.checkin import Checkin


async def deduplicate_episodes():
    """Find and remove duplicate episodes, preserving checkins."""
    async for db in get_db():
        print("🔍 Searching for duplicate episodes by tvdb_id...")

        # Find duplicate tvdb_ids
        stmt = (
            select(Episode.tvdb_id, func.count(Episode.id).label('count'))
            .group_by(Episode.tvdb_id)
            .having(func.count(Episode.id) > 1)
        )
        result = await db.execute(stmt)
        duplicate_tvdb_ids = [row[0] for row in result.all()]

        if not duplicate_tvdb_ids:
            print("✅ No duplicate episodes found!")
            return

        print(f"⚠️  Found {len(duplicate_tvdb_ids)} duplicate episode tvdb_ids")

        total_deleted = 0
        total_checkins_updated = 0

        for tvdb_id in duplicate_tvdb_ids:
            # Get all episodes with this tvdb_id, ordered by ID (oldest first)
            stmt = (
                select(Episode)
                .where(Episode.tvdb_id == tvdb_id)
                .order_by(Episode.id.asc())
            )
            result = await db.execute(stmt)
            episodes = result.scalars().all()

            if len(episodes) <= 1:
                continue

            # Keep the first (oldest) episode
            keep_episode = episodes[0]
            duplicate_episodes = episodes[1:]

            print(f"\n📺 Episode TVDB ID {tvdb_id}:")
            print(f"   Keeping: ID {keep_episode.id} - S{keep_episode.season_number}E{keep_episode.episode_number}: {keep_episode.name}")
            print(f"   Duplicates: {len(duplicate_episodes)}")

            # Update all checkins pointing to duplicates
            for dup_episode in duplicate_episodes:
                # Find checkins using this duplicate
                stmt = select(Checkin).where(Checkin.episode_id == dup_episode.id)
                result = await db.execute(stmt)
                checkins = result.scalars().all()

                if checkins:
                    print(f"     - Updating {len(checkins)} checkin(s) from episode ID {dup_episode.id} -> {keep_episode.id}")
                    for checkin in checkins:
                        checkin.episode_id = keep_episode.id
                    total_checkins_updated += len(checkins)

                # Delete the duplicate episode
                await db.delete(dup_episode)
                total_deleted += 1
                print(f"     - Deleted duplicate episode ID {dup_episode.id}")

        # Commit all changes
        await db.commit()

        print(f"\n✅ Deduplication complete!")
        print(f"   Episodes deleted: {total_deleted}")
        print(f"   Checkins updated: {total_checkins_updated}")


async def deduplicate_seasons():
    """Find and remove duplicate seasons by season_number, keeping only 'Aired Order' type."""
    async for db in get_db():
        print("\n🔍 Searching for duplicate seasons by (content_id, season_number)...")

        # Find all content with seasons
        stmt = select(Season.content_id).distinct()
        result = await db.execute(stmt)
        content_ids = [row[0] for row in result.all()]

        if not content_ids:
            print("✅ No seasons found!")
            return

        print(f"📊 Checking {len(content_ids)} content items for duplicate seasons...")

        total_deleted = 0
        total_episodes_updated = 0

        for content_id in content_ids:
            # Get all seasons for this content, grouped by season_number
            stmt = (
                select(Season)
                .where(Season.content_id == content_id)
                .order_by(Season.season_number, Season.id.asc())
            )
            result = await db.execute(stmt)
            all_seasons = result.scalars().all()

            # Group by season_number
            seasons_by_number = {}
            for season in all_seasons:
                if season.season_number not in seasons_by_number:
                    seasons_by_number[season.season_number] = []
                seasons_by_number[season.season_number].append(season)

            # Process each season_number group
            for season_number, seasons in seasons_by_number.items():
                if len(seasons) <= 1:
                    continue  # No duplicates

                # Prefer "Aired Order" (type_id = 1), otherwise keep oldest
                aired_order_seasons = [s for s in seasons if s.season_type_id == 1]
                keep_season = aired_order_seasons[0] if aired_order_seasons else seasons[0]
                duplicate_seasons = [s for s in seasons if s.id != keep_season.id]

                print(f"\n📅 Content {content_id} - Season {season_number}:")
                print(f"   Keeping: ID {keep_season.id} - {keep_season.season_type or 'Unknown'} (TVDB: {keep_season.tvdb_id})")
                print(f"   Duplicates: {len(duplicate_seasons)}")

                # Update all episodes pointing to duplicates
                for dup_season in duplicate_seasons:
                    # Find episodes using this duplicate season
                    stmt = select(Episode).where(Episode.season_id == dup_season.id)
                    result = await db.execute(stmt)
                    episodes = result.scalars().all()

                    if episodes:
                        print(f"     - Updating {len(episodes)} episode(s) from season ID {dup_season.id} -> {keep_season.id}")
                        for episode in episodes:
                            episode.season_id = keep_season.id
                        total_episodes_updated += len(episodes)

                    # Delete the duplicate season
                    await db.delete(dup_season)
                    total_deleted += 1
                    print(f"     - Deleted duplicate season ID {dup_season.id} ({dup_season.season_type})")

        # Commit all changes
        await db.commit()

        print(f"\n✅ Deduplication complete!")
        print(f"   Seasons deleted: {total_deleted}")
        print(f"   Episodes updated: {total_episodes_updated}")


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Episode & Season Deduplication Script")
    print("=" * 60)
    print()

    await deduplicate_episodes()
    await deduplicate_seasons()

    print("\n" + "=" * 60)
    print("✅ All done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
