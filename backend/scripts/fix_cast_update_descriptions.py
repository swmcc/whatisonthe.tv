#!/usr/bin/env python3
"""
Script to fix watchlist update descriptions where the character name was
incorrectly used as the content title.

Bug: When TVDB API returned character data without seriesName or movieName,
the code fell back to char.get("name") which is the character name. This caused
descriptions like "Dulé Hill cast in 'David' as David".

This script finds affected records and fixes them by looking up the correct
content name from the database or TVDB API.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to path (works locally and on Heroku)
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload

from app.core.config import settings
from app.models import Content
from app.models.watchlist_update import WatchlistUpdate, UpdateType
from app.services.tvdb import tvdb_service


async def fix_cast_update_descriptions(dry_run: bool = True):
    """
    Find and fix watchlist updates where character name was used as content name.

    Args:
        dry_run: If True, only report what would be changed without making changes.
    """
    print("=" * 60)
    print("FIX CAST UPDATE DESCRIPTIONS")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)

    # Create async engine
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Find all NEW_CAST updates
        stmt = (
            select(WatchlistUpdate)
            .where(WatchlistUpdate.update_type == UpdateType.NEW_CAST)
            .options(selectinload(WatchlistUpdate.watchlist_item))
        )
        result = await db.execute(stmt)
        updates = result.scalars().all()

        print(f"\nFound {len(updates)} NEW_CAST updates to check")

        fixed_count = 0
        skipped_count = 0

        for update in updates:
            details = update.details or {}
            content_name = details.get("content_name")
            character_name = details.get("character_name")
            content_tvdb_id = details.get("content_tvdb_id")

            # Check if this record has the bug:
            # content_name equals character_name (case-insensitive)
            if not content_name or not character_name:
                continue

            if content_name.lower() != character_name.lower():
                continue

            # This record likely has the bug - look up the correct name
            print(f"\n  Found affected record (id={update.id}):")
            print(f"    Current description: {update.description}")
            print(f"    content_name: {content_name}")
            print(f"    character_name: {character_name}")
            print(f"    content_tvdb_id: {content_tvdb_id}")

            if not content_tvdb_id:
                print("    SKIP: No content_tvdb_id to look up")
                skipped_count += 1
                continue

            # Look up correct name from DB first
            correct_name = None
            stmt = select(Content).where(Content.tvdb_id == content_tvdb_id)
            result = await db.execute(stmt)
            content = result.scalar_one_or_none()

            if content and content.name:
                correct_name = content.name
                print(f"    Found in DB: {correct_name}")
            else:
                # Try TVDB API - determine if series or movie from role_type or other hints
                # First try series, then movie
                print("    Not in DB, trying TVDB API...")
                api_data = tvdb_service.get_series_details(content_tvdb_id)
                if api_data and api_data.get("name"):
                    correct_name = api_data.get("name")
                    print(f"    Found series: {correct_name}")
                else:
                    api_data = tvdb_service.get_movie_details(content_tvdb_id)
                    if api_data and api_data.get("name"):
                        correct_name = api_data.get("name")
                        print(f"    Found movie: {correct_name}")

            if not correct_name:
                print("    SKIP: Could not find correct name")
                skipped_count += 1
                continue

            # Build corrected description
            # Extract person name from the original description
            # Format: '{person_name} cast in "{content_name}"' or with ' as {character}'
            old_desc = update.description

            # Try to extract person name - it's everything before ' cast in '
            if ' cast in "' in old_desc:
                person_name = old_desc.split(' cast in "')[0]
                new_desc = f'{person_name} cast in "{correct_name}"'
                if character_name and character_name != person_name:
                    new_desc += f' as {character_name}'

                print(f"    New description: {new_desc}")

                if not dry_run:
                    # Update the record
                    update.description = new_desc
                    update.details = {
                        **details,
                        "content_name": correct_name,
                    }
                    fixed_count += 1
            else:
                print("    SKIP: Unexpected description format")
                skipped_count += 1

        if not dry_run:
            await db.commit()

        print("\n" + "=" * 60)
        print("SUMMARY")
        print(f"  Records checked: {len(updates)}")
        print(f"  Records {'would be ' if dry_run else ''}fixed: {fixed_count}")
        print(f"  Records skipped: {skipped_count}")
        if dry_run:
            print("\nRun with --live to apply changes")
        print("=" * 60)


if __name__ == "__main__":
    dry_run = "--live" not in sys.argv

    if not dry_run:
        print("\n*** LIVE MODE - Changes will be saved ***\n")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(fix_cast_update_descriptions(dry_run=dry_run))
