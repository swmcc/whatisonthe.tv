#!/usr/bin/env python3
"""Resync all TV shows from TVDB to fix episode data."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.db.database import get_db
from app.models.content import Content
from app.tasks.content import sync_content_from_tvdb


async def resync_all_shows():
    """Resync all TV show content from TVDB."""
    async for db in get_db():
        print("=" * 60)
        print("RESYNC: Refreshing all TV shows from TVDB")
        print("=" * 60)

        # Get all series content
        stmt = select(Content).where(Content.content_type == 'series')
        result = await db.execute(stmt)
        shows = result.scalars().all()

        print(f"\nFound {len(shows)} TV shows to resync\n")

        for i, show in enumerate(shows, 1):
            print(f"{i}/{len(shows)} Resyncing: {show.name} (ID: {show.id}, TVDB: {show.tvdb_id})")
            try:
                # Call the sync function directly (not as Celery task)
                await sync_content_from_tvdb(db, show.tvdb_id, content_type='series', content_id=show.id)
                print(f"   ✓ Synced successfully")
            except Exception as e:
                print(f"   ✗ Error: {e}")

        await db.commit()
        print("\n✨ Resync complete!")
        break


if __name__ == "__main__":
    asyncio.run(resync_all_shows())
