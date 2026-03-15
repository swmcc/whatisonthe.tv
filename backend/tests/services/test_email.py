"""Tests for the email service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.email import EmailService, get_email_service, is_email_configured


class TestEmailService:
    """Tests for EmailService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.from_address = "test@example.com"
        self.from_name = "Test Sender"
        self.service = EmailService(
            api_key=self.api_key,
            from_address=self.from_address,
            from_name=self.from_name,
        )

    def test_init_stores_configuration(self):
        """Test that EmailService stores configuration correctly."""
        assert self.service.api_key == self.api_key
        assert self.service.from_address == self.from_address
        assert self.service.from_name == self.from_name
        assert self.service._client is None

    def test_formatted_from(self):
        """Test that formatted_from combines name and address."""
        expected = "Test Sender <test@example.com>"
        assert self.service.formatted_from == expected

    def test_client_is_singleton(self):
        """Test that client is only created once."""
        mock_client = MagicMock()
        self.service._client = mock_client

        # Access client multiple times
        client1 = self.service.client
        client2 = self.service.client

        # Should be same instance
        assert client1 is client2

    def test_send_calls_client_with_correct_params(self):
        """Test that send method calls client with correct parameters."""
        mock_client = MagicMock()
        mock_client.emails.send.return_value = {"id": "msg-123"}
        self.service._client = mock_client

        result = self.service.send(
            to="recipient@example.com",
            subject="Test Subject",
            html_body="<h1>Hello</h1>",
            text_body="Hello",
            reply_to="reply@example.com",
            tags=["test", "welcome"],
            metadata={"user_id": "123"},
        )

        mock_client.emails.send.assert_called_once_with(
            from_=self.service.formatted_from,
            to="recipient@example.com",
            subject="Test Subject",
            html="<h1>Hello</h1>",
            text="Hello",
            reply_to="reply@example.com",
            tags=["test", "welcome"],
            metadata={"user_id": "123"},
        )
        assert result == {"id": "msg-123"}

    def test_send_with_minimal_params(self):
        """Test send with only required parameters."""
        mock_client = MagicMock()
        mock_client.emails.send.return_value = {"id": "msg-456"}
        self.service._client = mock_client

        self.service.send(
            to="recipient@example.com",
            subject="Minimal Email",
            html_body="<p>Content</p>",
        )

        mock_client.emails.send.assert_called_once_with(
            from_=self.service.formatted_from,
            to="recipient@example.com",
            subject="Minimal Email",
            html="<p>Content</p>",
            text=None,
            reply_to=None,
            tags=None,
            metadata=None,
        )

    def test_send_batch_calls_client_correctly(self):
        """Test batch email sending."""
        mock_client = MagicMock()
        mock_client.emails.send_batch.return_value = {"sent": 2}
        self.service._client = mock_client

        emails = [
            {
                "to": "user1@example.com",
                "subject": "Email 1",
                "html": "<p>Hello User 1</p>",
            },
            {
                "to": "user2@example.com",
                "subject": "Email 2",
                "html": "<p>Hello User 2</p>",
                "text": "Hello User 2",
                "tags": ["batch"],
            },
        ]

        result = self.service.send_batch(emails)

        # Verify batch was constructed correctly
        call_args = mock_client.emails.send_batch.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["to"] == "user1@example.com"
        assert call_args[0]["from_"] == self.service.formatted_from
        assert call_args[1]["tags"] == ["batch"]
        assert result == {"sent": 2}

    def test_track_event_calls_client(self):
        """Test event tracking."""
        mock_client = MagicMock()
        mock_client.events.track.return_value = {"tracked": True}
        self.service._client = mock_client

        result = self.service.track_event(
            event_name="watchlist_added",
            user_email="user@example.com",
            properties={"content_id": "456"},
            session_id="sess-123",
        )

        mock_client.events.track.assert_called_once_with(
            event="watchlist_added",
            user={"email": "user@example.com"},
            properties={"content_id": "456"},
            session_id="sess-123",
        )
        assert result == {"tracked": True}

    def test_track_event_with_minimal_params(self):
        """Test event tracking with minimal parameters."""
        mock_client = MagicMock()
        mock_client.events.track.return_value = {"tracked": True}
        self.service._client = mock_client

        self.service.track_event(
            event_name="login",
            user_email="user@example.com",
        )

        mock_client.events.track.assert_called_once_with(
            event="login",
            user={"email": "user@example.com"},
            properties=None,
            session_id=None,
        )

    def test_upsert_contact_calls_client(self):
        """Test contact upsert."""
        mock_client = MagicMock()
        mock_client.contacts.upsert.return_value = {"id": "contact-123"}
        self.service._client = mock_client

        result = self.service.upsert_contact(
            email="newuser@example.com",
            first_name="New",
            last_name="User",
            tags=["premium", "active"],
            properties={"plan": "pro"},
        )

        mock_client.contacts.upsert.assert_called_once_with(
            email="newuser@example.com",
            first_name="New",
            last_name="User",
            tags=["premium", "active"],
            properties={"plan": "pro"},
        )
        assert result == {"id": "contact-123"}

    def test_upsert_contact_with_minimal_params(self):
        """Test contact upsert with minimal parameters."""
        mock_client = MagicMock()
        mock_client.contacts.upsert.return_value = {"id": "contact-456"}
        self.service._client = mock_client

        self.service.upsert_contact(email="minimal@example.com")

        mock_client.contacts.upsert.assert_called_once_with(
            email="minimal@example.com",
            first_name=None,
            last_name=None,
            tags=None,
            properties=None,
        )


class TestEmailServiceFactory:
    """Tests for email service factory functions."""

    def setup_method(self):
        """Reset singleton before each test."""
        import app.services.email as email_module

        email_module._email_service = None

    @patch("app.services.email.settings")
    def test_get_email_service_creates_instance(self, mock_settings):
        """Test that get_email_service creates an instance with settings."""
        mock_settings.mailjunky_api_key = "real-api-key"
        mock_settings.email_from_address = "app@example.com"
        mock_settings.email_from_name = "My App"

        service = get_email_service()

        assert isinstance(service, EmailService)
        assert service.api_key == "real-api-key"
        assert service.from_address == "app@example.com"
        assert service.from_name == "My App"

    @patch("app.services.email.settings")
    def test_get_email_service_returns_singleton(self, mock_settings):
        """Test that get_email_service returns same instance."""
        mock_settings.mailjunky_api_key = "api-key"
        mock_settings.email_from_address = "test@test.com"
        mock_settings.email_from_name = "Test"

        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2

    @patch("app.services.email.settings")
    def test_get_email_service_raises_when_not_configured(self, mock_settings):
        """Test that get_email_service raises ValueError when not configured."""
        mock_settings.mailjunky_api_key = ""

        with pytest.raises(ValueError, match="MAILJUNKY_API_KEY is not configured"):
            get_email_service()

    @patch("app.services.email.settings")
    def test_is_email_configured_true(self, mock_settings):
        """Test is_email_configured returns True when API key is set."""
        mock_settings.mailjunky_api_key = "some-key"

        assert is_email_configured() is True

    @patch("app.services.email.settings")
    def test_is_email_configured_false(self, mock_settings):
        """Test is_email_configured returns False when API key is empty."""
        mock_settings.mailjunky_api_key = ""

        assert is_email_configured() is False

    @patch("app.services.email.settings")
    def test_is_email_configured_false_when_none(self, mock_settings):
        """Test is_email_configured returns False when API key is None."""
        mock_settings.mailjunky_api_key = None

        assert is_email_configured() is False
