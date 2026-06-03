"""Sentry must stay OFF unless a DSN is configured (so dev/test never report)."""

import sentry_sdk

import app.main  # noqa: F401 — importing runs the (guarded) init block
from app.config import Settings


def test_sentry_dsn_defaults_empty():
    assert Settings().sentry_dsn == ""


def test_sentry_not_active_without_dsn():
    # The test environment has no SENTRY_DSN, so importing app.main must not
    # have initialised an active Sentry client.
    assert sentry_sdk.get_client().is_active() is False
