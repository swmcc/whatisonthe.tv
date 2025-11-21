#!/usr/bin/env python3
"""Seed checkins for the last month with realistic viewing patterns."""

import asyncio
import random
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.db.database import get_db
from app.models.content import Content
from app.models.episode import Episode
from app.models.checkin import Checkin
from app.models.user import User


async def seed_checkins():
    async for db in get_db():
        # Get the user
        result = await db.execute(select(User).where(User.email == "me@swm.cc"))
        user = result.scalar_one()

        # Get available content
        result = await db.execute(select(Content))
        all_content = result.scalars().all()

        series = [c for c in all_content if c.content_type == 'series']
        movies = [c for c in all_content if c.content_type == 'movie']

        print(f"📊 Found {len(series)} series and {len(movies)} movies")
        print(f"👤 Seeding checkins for user: {user.email}\n")

        # Get some episodes for series
        episode_cache = {}
        for show in series[:5]:  # Cache episodes for first few shows
            result = await db.execute(
                select(Episode).where(Episode.content_id == show.id).limit(30)
            )
            episodes = result.scalars().all()
            if episodes:
                episode_cache[show.id] = {
                    'name': show.name,
                    'episodes': episodes
                }

        # Generate checkins for last 30 days
        checkins_created = 0
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        current_date = start_date
        while current_date <= end_date:
            # 1-4 checkins per day
            num_checkins = random.randint(1, 4)

            for _ in range(num_checkins):
                # Random time of day (realistic viewing hours)
                hour = random.choice([9, 12, 14, 19, 20, 21, 22, 23])
                minute = random.randint(0, 59)
                watched_at = current_date.replace(hour=hour, minute=minute)

                # 70% series, 30% movies
                if random.random() < 0.7 and episode_cache:
                    # Pick a random series with cached episodes
                    show_id = random.choice(list(episode_cache.keys()))
                    show_data = episode_cache[show_id]
                    episode = random.choice(show_data['episodes'])

                    checkin = Checkin(
                        user_id=user.id,
                        content_id=show_id,
                        episode_id=episode.id,
                        watched_at=watched_at
                    )
                    db.add(checkin)
                    checkins_created += 1

                    ep_str = f"S{episode.season_number:02d}E{episode.episode_number:02d}"
                    print(f"  ✓ {watched_at.strftime('%Y-%m-%d %H:%M')} - {show_data['name']} {ep_str}")
                else:
                    # Movie checkin
                    if movies:
                        movie = random.choice(movies)
                        checkin = Checkin(
                            user_id=user.id,
                            content_id=movie.id,
                            watched_at=watched_at
                        )
                        db.add(checkin)
                        checkins_created += 1
                        print(f"  ✓ {watched_at.strftime('%Y-%m-%d %H:%M')} - {movie.name} (movie)")

            current_date += timedelta(days=1)

        await db.commit()
        print(f"\n✅ Created {checkins_created} checkins over 30 days")
        break


if __name__ == "__main__":
    asyncio.run(seed_checkins())
