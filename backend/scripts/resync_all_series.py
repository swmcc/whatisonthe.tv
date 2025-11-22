#!/usr/bin/env python3
"""
Resync all TV series to apply the new Aired Order filtering.

This script:
1. Finds all series content in the database
2. Clears their last_synced_at timestamp
3. Triggers a background re-sync for each series
4. The re-sync will apply the new "Aired Order only" logic
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, and_
from app.db.database import get_db
from app.models.content import Content
from app.models.series_detail import SeriesDetail
from app.tasks.content import save_series_full


async def resync_all_series(force: bool = False):
    """Find all series and trigger re-sync."""
    async for db in get_db():
        print("=" * 60)
        print("TV Series Re-sync Script")
        print("=" * 60)
        print()

        # Find all series content
        stmt = (
            select(Content)
            .join(SeriesDetail)
            .where(Content.content_type == 'series')
            .order_by(Content.id.asc())
        )
        result = await db.execute(stmt)
        all_series = result.scalars().all()

        if not all_series:
            print("✅ No series found in database!")
            return

        print(f"📊 Found {len(all_series)} TV series in database")
        print()

        if not force:
            print("⚠️  This will re-sync all series to apply new Aired Order filtering")
            response = input("Continue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Aborted")
                return
            print()

        total_synced = 0
        total_failed = 0

        for series in all_series:
            try:
                print(f"🔄 Re-syncing: {series.name} ({series.year}) [TVDB: {series.tvdb_id}]")

                # Clear last_synced_at to force re-sync
                series.last_synced_at = None
                await db.flush()

                # Queue background task to re-fetch with new logic
                # Note: In production with Celery, this will be async
                # For local testing without Celery, we might need to call directly
                try:
                    save_series_full.delay(series.tvdb_id, None)
                    print(f"   ✓ Queued for re-sync (background task)")
                except Exception as e:
                    # If Celery not available, log it
                    print(f"   ⚠️  Could not queue background task: {e}")
                    print(f"   ℹ️  Series will be re-synced on next API access")

                total_synced += 1

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                total_failed += 1

        # Commit all changes
        await db.commit()

        print()
        print("=" * 60)
        print("✅ Re-sync Complete!")
        print("=" * 60)
        print(f"  Series processed: {total_synced}")
        print(f"  Failed: {total_failed}")
        print()
        print("ℹ️  Note: Background tasks will fetch new data over the next few minutes")
        print("ℹ️  Duplicate seasons will be prevented by the new filtering logic")


async def main():
    """Main entry point."""
    force = '--force' in sys.argv or '-f' in sys.argv

    await resync_all_series(force)


if __name__ == "__main__":
    asyncio.run(main())
