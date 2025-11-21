#!/usr/bin/env python3
"""Queue resync tasks for all TV shows on production (Heroku)."""

import subprocess
import sys

# Python script to run on Heroku
heroku_script = """
from app.db.database import SyncSessionLocal
from app.models.content import Content
from app.tasks.content import save_series_full
from sqlalchemy import select

with SyncSessionLocal() as db:
    # Get all series content
    stmt = select(Content).where(Content.content_type == 'series')
    result = db.execute(stmt)
    shows = result.scalars().all()

    print(f"Found {len(shows)} TV shows to resync")
    print("=" * 60)

    queued_count = 0
    for show in shows:
        try:
            task = save_series_full.delay(show.tvdb_id)
            print(f"✓ Queued: {show.name} (TVDB: {show.tvdb_id}) - Task: {task.id}")
            queued_count += 1
        except Exception as e:
            print(f"✗ Failed to queue {show.name}: {e}")

    print("=" * 60)
    print(f"Queued {queued_count}/{len(shows)} shows for resync")
    print("Worker will process them with 5-15 second delays between each")
"""

print("🚀 Starting production resync...")
print("This will queue all TV shows for background resync on Heroku")
print()

# Run on Heroku
cmd = ["heroku", "run", "-a", "whatisonthe-tv", f"python -c '{heroku_script}'"]
result = subprocess.run(cmd, capture_output=False, text=True)

sys.exit(result.returncode)
