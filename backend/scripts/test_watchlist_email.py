#!/usr/bin/env python
"""Test watchlist email generation.

Usage:
    python scripts/test_watchlist_email.py
    python scripts/test_watchlist_email.py --user-id 1
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tasks.email_notifications import send_test_watchlist_email, send_daily_watchlist_emails


def main() -> None:
    parser = argparse.ArgumentParser(description="Test watchlist email")
    parser.add_argument(
        "--user-id",
        type=int,
        help="Send test email to specific user ID",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the full daily email task",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("Watchlist Email Test")
    print("=" * 50)

    if args.all:
        print("\nRunning daily watchlist email task...")
        result = send_daily_watchlist_emails()
        print(f"\nResult: {result}")
    elif args.user_id:
        print(f"\nSending test email to user {args.user_id}...")
        result = send_test_watchlist_email(args.user_id)
        print(f"\nResult: {result}")
    else:
        print("\nUsage:")
        print("  --user-id N  Send test email to user N")
        print("  --all        Run full daily email task")
        print("\nExample:")
        print("  python scripts/test_watchlist_email.py --user-id 1")

    print()
    print("📧 View emails at: http://localhost:8000/_mail")


if __name__ == "__main__":
    main()
