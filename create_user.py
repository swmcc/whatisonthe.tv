#!/usr/bin/env python3
"""Create a user in the production database."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select


async def create_user(email: str, username: str, password: str):
    """Create a user in the database."""
    async for db in get_db():
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User with email {email} already exists (ID: {existing_user.id})")
            return

        # Create new user
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✓ User created successfully!")
        print(f"  Email: {user.email}")
        print(f"  Username: {user.username}")
        print(f"  ID: {user.id}")
        break


if __name__ == "__main__":
    email = "me@swm.cc"
    username = "swm"
    password = "password5"

    print(f"Creating user: {email}")
    asyncio.run(create_user(email, username, password))
