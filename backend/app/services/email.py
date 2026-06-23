"""Transactional email via Resend."""

from __future__ import annotations

import resend

from app.config import get_settings


def send_email(*, to: str, subject: str, html: str) -> str:
    """Send a transactional email. Returns the Resend message id."""
    settings = get_settings()
    resend.api_key = settings.resend_api_key
    response = resend.Emails.send(
        {
            "from": settings.resend_from_email,
            "to": to,
            "subject": subject,
            "html": html,
        }
    )
    return response["id"]
