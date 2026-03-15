#!/usr/bin/env python
"""Send a test email to verify email integration.

Usage:
    python scripts/send_test_email.py
    python scripts/send_test_email.py --to user@example.com
    python scripts/send_test_email.py --subject "Custom Subject"
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mailview import Email, EmailStore


async def send_test_email(to: str, subject: str) -> None:
    """Send a test email to mailview."""
    html_body = """
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #4a90d9;">🎬 Test Email</h1>
        <p>This is a test email from <strong>What Is On The TV</strong>.</p>
        <p>If you're seeing this in mailview, your email integration is working!</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <h2>Features Available:</h2>
        <ul>
            <li>✅ Send single emails</li>
            <li>✅ Send batch emails</li>
            <li>✅ Track user events</li>
            <li>✅ Manage contacts</li>
        </ul>
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px;">
            <h3 style="margin-top: 0;">Next Steps:</h3>
            <ol>
                <li>Set <code>MAILJUNKY_API_KEY</code> in your <code>.env</code></li>
                <li>Use <code>get_email_service()</code> to send real emails</li>
                <li>Emails will be captured here in development</li>
            </ol>
        </div>
        <p style="color: #666; font-size: 12px; margin-top: 20px;">
            Sent via mailview development preview
        </p>
    </div>
    """

    text_body = """
Test Email from What Is On The TV
==================================

This is a test email. If you're seeing this in mailview,
your email integration is working!

Features Available:
- Send single emails
- Send batch emails
- Track user events
- Manage contacts

Next Steps:
1. Set MAILJUNKY_API_KEY in your .env
2. Use get_email_service() to send real emails
3. Emails will be captured here in development

---
Sent via mailview development preview
    """

    email = Email(
        sender="What Is On The TV <noreply@whatisonthe.tv>",
        to=[to],
        subject=subject,
        html_body=html_body,
        text_body=text_body,
    )

    store = EmailStore()
    await store.save(email)

    print(f"✅ Email sent successfully!")
    print(f"   ID: {email.id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a test email to mailview")
    parser.add_argument(
        "--to",
        default="test@example.com",
        help="Recipient email address (default: test@example.com)",
    )
    parser.add_argument(
        "--subject",
        default="🎬 Test Email from What Is On The TV",
        help="Email subject line",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("Email Integration Test")
    print("=" * 50)
    print(f"To: {args.to}")
    print(f"Subject: {args.subject}")
    print()

    asyncio.run(send_test_email(to=args.to, subject=args.subject))

    print()
    print("📧 View the email at: http://localhost:8000/_mail")


if __name__ == "__main__":
    main()
