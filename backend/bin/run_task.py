#!/usr/bin/env python
"""CLI script to trigger Celery tasks in production."""

import sys

from app.workers.celery_app import celery_app


TASKS = {
    "watchlist": "app.tasks.watchlist_updates.check_watchlist_updates",
    "email": "app.tasks.email_notifications.send_daily_watchlist_emails",
    "refresh": "app.tasks.scheduled.refresh_stale_content",
    "cleanup": "app.tasks.scheduled.cleanup_old_sync_logs",
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m bin.run_task <task_name>")
        print("\nAvailable tasks:")
        for name, full_name in TASKS.items():
            print(f"  {name:12} -> {full_name}")
        sys.exit(1)

    task_name = sys.argv[1]

    if task_name not in TASKS:
        print(f"Unknown task: {task_name}")
        print(f"Available: {', '.join(TASKS.keys())}")
        sys.exit(1)

    full_task_name = TASKS[task_name]
    print(f"Queuing task: {full_task_name}")

    result = celery_app.send_task(full_task_name)
    print(f"Task queued with ID: {result.id}")


if __name__ == "__main__":
    main()
