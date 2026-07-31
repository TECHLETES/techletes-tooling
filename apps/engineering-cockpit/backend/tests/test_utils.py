"""Tests for backend/utils/utils.py email utilities."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from backend.utils.utils import (
    EmailData,
    generate_password_reset_token,
    generate_reset_password_email,
    generate_test_email,
    render_email_template,
    send_email,
    verify_password_reset_token,
)


class TestEmailDataclass:
    """Test EmailData dataclass."""

    def test_email_data_creation(self) -> None:
        """Test creating EmailData instance."""
        html = "<h1>Test</h1>"
        subject = "Test Subject"
        email_data = EmailData(html_content=html, subject=subject)
        assert email_data.html_content == html
        assert email_data.subject == subject


class TestRenderEmailTemplate:
    """Test email template rendering."""

    @patch("backend.utils.utils.Path")
    @patch("backend.utils.utils.Template")
    def test_render_email_template(self, mock_template_class, mock_path) -> None:
        """Test rendering an email template."""
        mock_file = MagicMock()
        mock_file.read_text.return_value = "<h1>{{ project_name }}</h1>"
        mock_path.return_value.__truediv__.return_value = mock_file

        mock_template = MagicMock()
        mock_template.render.return_value = "<h1>My Project</h1>"
        mock_template_class.return_value = mock_template

        result = render_email_template(
            template_name="test.html", context={"project_name": "My Project"}
        )

        assert result == "<h1>My Project</h1>"
        mock_template.render.assert_called_once_with({"project_name": "My Project"})


class TestSendEmail:
    """Test send_email function."""

    @patch("backend.utils.utils.settings")
    @patch("backend.utils.utils.emails.Message")
    @patch("backend.utils.utils.logger")
    def test_send_email_success(
        self, mock_logger, mock_message_class, mock_settings
    ) -> None:
        """Test successful email sending."""
        mock_settings.emails_enabled = True
        mock_settings.EMAILS_FROM_NAME = "Test"
        mock_settings.EMAILS_FROM_EMAIL = "test@example.com"
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 1025
        mock_settings.SMTP_TLS = False
        mock_settings.SMTP_SSL = False
        mock_settings.SMTP_USER = None
        mock_settings.SMTP_PASSWORD = None

        mock_message = MagicMock()
        mock_message_class.return_value = mock_message
        mock_message.send.return_value = True

        send_email(
            email_to="user@example.com", subject="Test", html_content="<h1>Test</h1>"
        )

        mock_message_class.assert_called_once()
        mock_message.send.assert_called_once()

    @patch("backend.utils.utils.settings")
    def test_send_email_disabled(self, mock_settings) -> None:
        """Test that send_email raises assertion when emails disabled."""
        mock_settings.emails_enabled = False

        with pytest.raises(AssertionError):
            send_email(
                email_to="user@example.com",
                subject="Test",
                html_content="<h1>Test</h1>",
            )

    @patch("backend.utils.utils.settings")
    @patch("backend.utils.utils.emails.Message")
    def test_send_email_with_tls_and_auth(
        self, mock_message_class, mock_settings
    ) -> None:
        """Test email sending with TLS and authentication."""
        mock_settings.emails_enabled = True
        mock_settings.EMAILS_FROM_NAME = "Test"
        mock_settings.EMAILS_FROM_EMAIL = "test@example.com"
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 1025
        mock_settings.SMTP_TLS = True
        mock_settings.SMTP_SSL = False
        mock_settings.SMTP_USER = "user"
        mock_settings.SMTP_PASSWORD = "pass"

        mock_message = MagicMock()
        mock_message_class.return_value = mock_message

        send_email(
            email_to="user@example.com", subject="Test", html_content="<h1>Test</h1>"
        )

        # Verify that send was called with TLS config
        call_args = mock_message.send.call_args
        assert call_args[1]["smtp"]["tls"] is True
        assert call_args[1]["smtp"]["user"] == "user"
        assert call_args[1]["smtp"]["password"] == "pass"

    @patch("backend.utils.utils.settings")
    @patch("backend.utils.utils.emails.Message")
    def test_send_email_with_ssl(self, mock_message_class, mock_settings) -> None:
        """Test email sending with SSL."""
        mock_settings.emails_enabled = True
        mock_settings.EMAILS_FROM_NAME = "Test"
        mock_settings.EMAILS_FROM_EMAIL = "test@example.com"
        mock_settings.SMTP_HOST = "localhost"
        mock_settings.SMTP_PORT = 1025
        mock_settings.SMTP_TLS = False
        mock_settings.SMTP_SSL = True
        mock_settings.SMTP_USER = None
        mock_settings.SMTP_PASSWORD = None

        mock_message = MagicMock()
        mock_message_class.return_value = mock_message

        send_email(
            email_to="user@example.com", subject="Test", html_content="<h1>Test</h1>"
        )

        # Verify that send was called with SSL config
        call_args = mock_message.send.call_args
        assert call_args[1]["smtp"]["ssl"] is True


class TestGenerateTestEmail:
    """Test generate_test_email function."""

    @patch("backend.utils.utils.render_email_template")
    @patch("backend.utils.utils.settings")
    def test_generate_test_email(self, mock_settings, mock_render) -> None:
        """Test generating test email."""
        mock_settings.PROJECT_NAME = "Test Project"
        mock_render.return_value = "<h1>Test Email</h1>"

        result = generate_test_email("user@example.com")

        assert isinstance(result, EmailData)
        assert result.subject == "Test Project - Test email"
        assert result.html_content == "<h1>Test Email</h1>"
        mock_render.assert_called_once()


class TestGenerateResetPasswordEmail:
    """Test generate_reset_password_email function."""

    @patch("backend.utils.utils.render_email_template")
    @patch("backend.utils.utils.settings")
    def test_generate_reset_password_email(self, mock_settings, mock_render) -> None:
        """Test generating password reset email."""
        mock_settings.PROJECT_NAME = "Test Project"
        mock_settings.FRONTEND_HOST = "http://localhost:3000"
        mock_settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS = 24
        mock_render.return_value = (
            "<a href='http://localhost:3000/reset-password?token=abc123'>Reset</a>"
        )

        result = generate_reset_password_email(
            email_to="user@example.com", email="user@example.com", token="abc123"
        )

        assert isinstance(result, EmailData)
        assert "Password recovery" in result.subject
        assert "user@example.com" in result.subject
        mock_render.assert_called_once()
        call_args = mock_render.call_args
        assert call_args[1]["context"]["valid_hours"] == 24
        assert "token=abc123" in call_args[1]["context"]["link"]


class TestGeneratePasswordResetToken:
    """Test password reset token generation."""

    @patch("backend.utils.utils.jwt.encode")
    @patch("backend.utils.utils.settings")
    def test_generate_password_reset_token(self, mock_settings, mock_encode) -> None:
        """Test generating password reset token."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS = 24
        mock_encode.return_value = "encoded-token-123"

        result = generate_password_reset_token("user@example.com")

        assert result == "encoded-token-123"
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args
        assert call_args[0][0]["sub"] == "user@example.com"
        assert "exp" in call_args[0][0]
        assert "nbf" in call_args[0][0]

    @patch("backend.utils.utils.jwt.encode")
    @patch("backend.utils.utils.settings")
    def test_generate_password_reset_token_expiry(
        self, mock_settings, mock_encode
    ) -> None:
        """Test that token has correct expiry."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS = 24
        mock_encode.return_value = "token"

        before = datetime.now(UTC)
        generate_password_reset_token("user@example.com")
        after = datetime.now(UTC)

        call_args = mock_encode.call_args
        token_data = call_args[0][0]
        exp_time = datetime.fromtimestamp(token_data["exp"], tz=UTC)

        # Verify expiry is approximately 24 hours from now
        expected_min = before + timedelta(hours=23.9)
        expected_max = after + timedelta(hours=24.1)
        assert expected_min <= exp_time <= expected_max


class TestVerifyPasswordResetToken:
    """Test password reset token verification."""

    @patch("backend.utils.utils.jwt.decode")
    @patch("backend.utils.utils.settings")
    def test_verify_password_reset_token_valid(
        self, mock_settings, mock_decode
    ) -> None:
        """Test verifying a valid password reset token."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_decode.return_value = {"sub": "user@example.com"}

        result = verify_password_reset_token("valid-token")

        assert result == "user@example.com"
        mock_decode.assert_called_once()

    @patch("backend.utils.utils.jwt.decode")
    @patch("backend.utils.utils.settings")
    def test_verify_password_reset_token_invalid(
        self, mock_settings, mock_decode
    ) -> None:
        """Test verifying an invalid password reset token."""
        from jwt.exceptions import InvalidTokenError

        mock_settings.SECRET_KEY = "test-secret-key"
        mock_decode.side_effect = InvalidTokenError("Invalid token")

        result = verify_password_reset_token("invalid-token")

        assert result is None

    @patch("backend.utils.utils.jwt.decode")
    @patch("backend.utils.utils.settings")
    def test_verify_password_reset_token_expired(
        self, mock_settings, mock_decode
    ) -> None:
        """Test verifying an expired password reset token."""
        from jwt.exceptions import ExpiredSignatureError

        mock_settings.SECRET_KEY = "test-secret-key"
        mock_decode.side_effect = ExpiredSignatureError("Token expired")

        result = verify_password_reset_token("expired-token")

        assert result is None

    @patch("backend.utils.utils.jwt.decode")
    @patch("backend.utils.utils.settings")
    def test_verify_password_reset_token_returns_string(
        self, mock_settings, mock_decode
    ) -> None:
        """Test that verify always returns a string, not the decoded object."""
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_decode.return_value = {"sub": 12345}

        result = verify_password_reset_token("token")

        assert isinstance(result, str)
        assert result == "12345"
