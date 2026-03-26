"""Celery tasks for sending email notifications."""

from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import SyncSessionLocal
from app.models.user import User
from app.models.watchlist_update import WatchlistUpdate, UpdateType
from app.services.email import get_email_service, is_email_configured
from app.workers.celery_app import celery_app


def _get_update_icon(update_type: UpdateType) -> str:
    """Get emoji icon for update type."""
    icons = {
        UpdateType.STATUS_CHANGE: "📺",
        UpdateType.NEW_EPISODE: "🎬",
        UpdateType.NEW_CAST: "⭐",
        UpdateType.METADATA_UPDATE: "ℹ️",
    }
    return icons.get(update_type, "📌")


def _get_update_category(update_type: UpdateType) -> str:
    """Get human-readable category for update type."""
    categories = {
        UpdateType.STATUS_CHANGE: "Status Changes",
        UpdateType.NEW_EPISODE: "New Episodes & Seasons",
        UpdateType.NEW_CAST: "Cast Updates",
        UpdateType.METADATA_UPDATE: "Other Updates",
    }
    return categories.get(update_type, "Updates")


def _build_email_html(user: User, updates: Sequence[WatchlistUpdate]) -> str:
    """Build HTML email content for watchlist updates."""
    # Group updates by type
    grouped: dict[UpdateType, list[WatchlistUpdate]] = {}
    for update in updates:
        if update.update_type not in grouped:
            grouped[update.update_type] = []
        grouped[update.update_type].append(update)

    # Build update sections
    sections_html = ""
    for update_type in [UpdateType.NEW_EPISODE, UpdateType.STATUS_CHANGE, UpdateType.NEW_CAST, UpdateType.METADATA_UPDATE]:
        if update_type not in grouped:
            continue

        type_updates = grouped[update_type]
        icon = _get_update_icon(update_type)
        category = _get_update_category(update_type)

        items_html = ""
        for update in type_updates:
            items_html += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #eee;">
                    <div style="font-weight: 500; color: #333;">{update.description}</div>
                    <div style="font-size: 12px; color: #888; margin-top: 4px;">
                        {update.created_at.strftime("%b %d at %I:%M %p")}
                    </div>
                </td>
            </tr>
            """

        sections_html += f"""
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 16px; color: #4a90d9; margin: 0 0 12px 0;">
                {icon} {category} ({len(type_updates)})
            </h2>
            <table style="width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                {items_html}
            </table>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="text-align: center; padding: 20px 0;">
                <h1 style="margin: 0; color: #333; font-size: 24px;">🎬 What Is On The TV</h1>
                <p style="margin: 8px 0 0 0; color: #666;">Your Daily Watchlist Update</p>
            </div>

            <!-- Greeting -->
            <div style="background: linear-gradient(135deg, #4a90d9 0%, #357abd 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 24px;">
                <h2 style="margin: 0 0 8px 0; font-size: 18px;">
                    Hey {user.first_name}! 👋
                </h2>
                <p style="margin: 0; opacity: 0.9;">
                    You have <strong>{len(updates)} update{"s" if len(updates) != 1 else ""}</strong> on your watchlist.
                </p>
            </div>

            <!-- Updates -->
            {sections_html}

            <!-- Footer -->
            <div style="text-align: center; padding: 20px 0; color: #888; font-size: 12px;">
                <p style="margin: 0;">
                    You're receiving this because you have items on your watchlist.
                </p>
                <p style="margin: 8px 0 0 0;">
                    <a href="#" style="color: #4a90d9;">View in app</a> •
                    <a href="#" style="color: #4a90d9;">Manage preferences</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """


def _build_email_text(user: User, updates: Sequence[WatchlistUpdate]) -> str:
    """Build plain text email content for watchlist updates."""
    lines = [
        "What Is On The TV - Daily Watchlist Update",
        "=" * 45,
        "",
        f"Hey {user.first_name}!",
        f"You have {len(updates)} update{'s' if len(updates) != 1 else ''} on your watchlist.",
        "",
    ]

    # Group updates by type
    grouped: dict[UpdateType, list[WatchlistUpdate]] = {}
    for update in updates:
        if update.update_type not in grouped:
            grouped[update.update_type] = []
        grouped[update.update_type].append(update)

    for update_type in [UpdateType.NEW_EPISODE, UpdateType.STATUS_CHANGE, UpdateType.NEW_CAST, UpdateType.METADATA_UPDATE]:
        if update_type not in grouped:
            continue

        type_updates = grouped[update_type]
        category = _get_update_category(update_type)

        lines.append(f"{category} ({len(type_updates)})")
        lines.append("-" * 30)

        for update in type_updates:
            lines.append(f"• {update.description}")

        lines.append("")

    lines.extend([
        "---",
        "You're receiving this because you have items on your watchlist.",
    ])

    return "\n".join(lines)


@celery_app.task(bind=True, max_retries=3)
def send_daily_watchlist_emails(self) -> dict[str, Any]:
    """
    Send daily watchlist update emails to users with unread updates.

    Only sends if the user has unread updates from the past 24 hours.
    This task should run daily via Celery beat.
    """
    print("=" * 60)
    print("DAILY WATCHLIST EMAIL TASK STARTED")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Check if email is configured for production
    if not is_email_configured():
        print("📧 Development mode - emails will be captured in mailview")

    email_service = get_email_service()

    emails_sent = 0
    errors = []

    with SyncSessionLocal() as db:
        # Get time threshold (last 24 hours)
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        # Find users with unread updates in the last 24 hours
        stmt = (
            select(User)
            .join(WatchlistUpdate)
            .where(
                WatchlistUpdate.is_read == False,  # noqa: E712
                WatchlistUpdate.created_at >= since,
            )
            .distinct()
        )
        result = db.execute(stmt)
        users = result.scalars().all()

        print(f"\nFound {len(users)} user(s) with unread updates")

        for user in users:
            # Get unread updates for this user
            stmt = (
                select(WatchlistUpdate)
                .where(
                    WatchlistUpdate.user_id == user.id,
                    WatchlistUpdate.is_read == False,  # noqa: E712
                    WatchlistUpdate.created_at >= since,
                )
                .options(selectinload(WatchlistUpdate.watchlist_item))
                .order_by(WatchlistUpdate.created_at.desc())
            )
            result = db.execute(stmt)
            updates = result.scalars().all()

            if not updates:
                continue

            print(f"\n  {user.email}: {len(updates)} update(s)")

            try:
                # Build email content
                html_body = _build_email_html(user, updates)
                text_body = _build_email_text(user, updates)

                # Send email
                email_service.send(
                    to=user.email,
                    subject=f"🎬 {len(updates)} update{'s' if len(updates) != 1 else ''} on your watchlist",
                    html_body=html_body,
                    text_body=text_body,
                    tags=["watchlist", "daily-digest"],
                    metadata={"user_id": str(user.id), "update_count": len(updates)},
                )

                emails_sent += 1
                print("    ✅ Email sent!")

            except Exception as e:
                # Try to get more details from the exception
                error_detail = str(e)
                if hasattr(e, 'response'):
                    try:
                        error_detail = f"{e} - Response: {e.response.text}"
                    except Exception:
                        pass
                error_msg = f"Failed to send email to {user.email}: {error_detail}"
                print(f"    ❌ {error_msg}")
                errors.append(error_msg)

    print("\n" + "=" * 60)
    print("DAILY WATCHLIST EMAIL TASK COMPLETE")
    print(f"Emails sent: {emails_sent}")
    if errors:
        print(f"Errors: {len(errors)}")
    print("=" * 60)

    return {
        "status": "success" if not errors else "partial",
        "emails_sent": emails_sent,
        "errors": errors,
    }


@celery_app.task
def send_test_watchlist_email(user_id: int) -> dict[str, Any]:
    """
    Send a test watchlist email to a specific user.

    Useful for testing the email format without waiting for the daily task.
    """
    email_service = get_email_service()

    with SyncSessionLocal() as db:
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return {"status": "error", "message": f"User {user_id} not found"}

        # Get recent updates (read or unread)
        stmt = (
            select(WatchlistUpdate)
            .where(WatchlistUpdate.user_id == user.id)
            .options(selectinload(WatchlistUpdate.watchlist_item))
            .order_by(WatchlistUpdate.created_at.desc())
            .limit(10)
        )
        result = db.execute(stmt)
        updates = result.scalars().all()

        if not updates:
            return {"status": "error", "message": "No watchlist updates found for user"}

        # Build and send email
        html_body = _build_email_html(user, updates)
        text_body = _build_email_text(user, updates)

        email_service.send(
            to=user.email,
            subject=f"🎬 [TEST] {len(updates)} update{'s' if len(updates) != 1 else ''} on your watchlist",
            html_body=html_body,
            text_body=text_body,
            tags=["watchlist", "test"],
            metadata={"user_id": str(user.id), "test": True},
        )

        return {
            "status": "success",
            "message": f"Test email sent to {user.email}",
            "update_count": len(updates),
        }
