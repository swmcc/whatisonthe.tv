#!/usr/bin/env python3
"""Simple script to get an auth token."""

import getpass
import httpx
import sys

API_URL = "http://localhost:8000"

def get_token(email: str, password: str) -> str:
    """Get auth token from API."""
    response = httpx.post(
        f"{API_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)

    data = response.json()
    return data["access_token"]


if __name__ == "__main__":
    print("🔐 Get Authentication Token\n")

    email = input("Email: ")
    password = getpass.getpass("Password: ")

    token = get_token(email, password)
    print(f"\n✅ Token: {token}")
    print(f"\nYou can now run:")
    print(f"  python import_netflix.py ~/Downloads/NetflixViewingHistory.csv {token} 25")
