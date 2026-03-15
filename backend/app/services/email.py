"""Email service for sending transactional emails via MailJunky."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from app.core.config import settings

if TYPE_CHECKING:
    import mailjunky


def _capture_to_mailview(
    from_addr: str,
    to: str,
    subject: str,
    html: Optional[str],
    text: Optional[str],
) -> str:
    """Capture email to mailview for development preview."""
    from mailview import Email, EmailStore

    async def _save():
        email = Email(
            sender=from_addr,
            to=[to] if isinstance(to, str) else list(to),
            subject=subject,
            html_body=html,
            text_body=text,
        )
        store = EmailStore()
        await store.save(email)
        return email.id

    return asyncio.run(_save())


class EmailService:
    """Email service using MailJunky SDK."""

    def __init__(
        self,
        api_key: str,
        from_address: str,
        from_name: str,
    ):
        self.api_key = api_key
        self.from_address = from_address
        self.from_name = from_name
        self._client: Optional[mailjunky.Client] = None

    @property
    def client(self) -> mailjunky.Client:
        """Lazy-load the MailJunky client."""
        if self._client is None:
            import mailjunky as mj

            self._client = mj.Client(api_key=self.api_key)
        return self._client

    @property
    def formatted_from(self) -> str:
        """Format from address with name."""
        return f"{self.from_name} <{self.from_address}>"

    def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Send a transactional email.

        In development mode (debug=True), emails are automatically captured
        to mailview for preview at /_mail.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_body: HTML content of the email
            text_body: Plain text fallback (optional)
            reply_to: Reply-to address (optional)
            tags: List of tags for categorization (optional)
            metadata: Additional metadata to attach (optional)

        Returns:
            Response dict with message ID
        """
        # In debug mode, capture to mailview
        if settings.debug:
            email_id = _capture_to_mailview(
                from_addr=self.formatted_from,
                to=to,
                subject=subject,
                html=html_body,
                text=text_body,
            )
            return {"id": email_id, "captured": True, "mailview": True}

        # In production, send via mailjunky API
        return self.client.emails.send(
            from_=self.formatted_from,
            to=to,
            subject=subject,
            html=html_body,
            text=text_body,
            reply_to=reply_to,
            tags=tags,
            metadata=metadata,
        )

    def send_batch(
        self,
        emails: list[dict],
    ) -> dict:
        """
        Send multiple emails in a batch.

        Args:
            emails: List of email dicts with keys: to, subject, html, text (optional)

        Returns:
            Response dict
        """
        # In debug mode, capture all to mailview
        if settings.debug:
            captured_ids = []
            for email in emails:
                email_id = _capture_to_mailview(
                    from_addr=self.formatted_from,
                    to=email["to"],
                    subject=email["subject"],
                    html=email.get("html"),
                    text=email.get("text"),
                )
                captured_ids.append(email_id)
            return {"ids": captured_ids, "captured": True, "mailview": True}

        # In production, send via mailjunky API
        batch = []
        for email in emails:
            batch.append({
                "from_": self.formatted_from,
                "to": email["to"],
                "subject": email["subject"],
                "html": email.get("html"),
                "text": email.get("text"),
                "tags": email.get("tags"),
                "metadata": email.get("metadata"),
            })
        return self.client.emails.send_batch(batch)

    def track_event(
        self,
        event_name: str,
        user_email: str,
        properties: Optional[dict] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Track a user event for workflow automation.

        Args:
            event_name: Name of the event (e.g., "watchlist_added")
            user_email: Email address of the user
            properties: Additional event properties
            session_id: Session identifier for grouping events

        Returns:
            Response from MailJunky API
        """
        # Events don't make sense to capture in debug mode
        if settings.debug:
            return {"event": event_name, "skipped": True, "debug": True}

        return self.client.events.track(
            event=event_name,
            user={"email": user_email},
            properties=properties,
            session_id=session_id,
        )

    def upsert_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        tags: Optional[list[str]] = None,
        properties: Optional[dict] = None,
    ) -> dict:
        """
        Create or update a contact.

        Args:
            email: Contact email address
            first_name: Contact first name (optional)
            last_name: Contact last name (optional)
            tags: List of tags (optional)
            properties: Additional contact properties (optional)

        Returns:
            Response from MailJunky API
        """
        # Contacts don't make sense to manage in debug mode
        if settings.debug:
            return {"email": email, "skipped": True, "debug": True}

        return self.client.contacts.upsert(
            email=email,
            first_name=first_name,
            last_name=last_name,
            tags=tags,
            properties=properties,
        )


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        # In debug mode, we don't require an API key
        if settings.debug:
            _email_service = EmailService(
                api_key="",
                from_address=settings.email_from_address,
                from_name=settings.email_from_name,
            )
        else:
            if not settings.mailjunky_api_key:
                raise ValueError("MAILJUNKY_API_KEY is not configured")
            _email_service = EmailService(
                api_key=settings.mailjunky_api_key,
                from_address=settings.email_from_address,
                from_name=settings.email_from_name,
            )
    return _email_service


def is_email_configured() -> bool:
    """Check if email service is configured for production use."""
    return bool(settings.mailjunky_api_key)
