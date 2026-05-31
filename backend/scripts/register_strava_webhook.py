#!/usr/bin/env python3
"""One-time script to register the Strava push-subscription for this app.

Run once per environment (local → staging → production). Strava allows only
one active subscription per client_id; this script is idempotent — it prints
the existing subscription id if one already exists.

Usage:
    cd backend
    STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... \
    STRAVA_WEBHOOK_VERIFY_TOKEN=... \
    BACKEND_PUBLIC_URL=https://evovlerun-production.up.railway.app \
    python scripts/register_strava_webhook.py

Or just run it with the env already set in your shell / Railway dashboard.
"""

import os
import sys

import httpx

PUSH_SUBSCRIPTIONS_URL = "https://www.strava.com/api/v3/push_subscriptions"


def main() -> None:
    client_id = os.environ.get("STRAVA_CLIENT_ID", "")
    client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")
    verify_token = os.environ.get("STRAVA_WEBHOOK_VERIFY_TOKEN", "")
    backend_url = os.environ.get("BACKEND_PUBLIC_URL", "").rstrip("/")

    missing = [k for k, v in {
        "STRAVA_CLIENT_ID": client_id,
        "STRAVA_CLIENT_SECRET": client_secret,
        "STRAVA_WEBHOOK_VERIFY_TOKEN": verify_token,
        "BACKEND_PUBLIC_URL": backend_url,
    }.items() if not v]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    callback_url = f"{backend_url}/providers/strava/webhook"
    print(f"Registering Strava webhook → {callback_url}")

    resp = httpx.post(PUSH_SUBSCRIPTIONS_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "callback_url": callback_url,
        "verify_token": verify_token,
    }, timeout=15)

    if resp.status_code == 201:
        sub = resp.json()
        print(f"✓ Subscription created — id: {sub.get('id')} (save this for reference)")
    elif resp.status_code == 409:
        print("Subscription already exists for this client_id.")
        # Fetch existing subscription to show the id.
        get_resp = httpx.get(PUSH_SUBSCRIPTIONS_URL, params={
            "client_id": client_id, "client_secret": client_secret,
        }, timeout=10)
        if get_resp.status_code == 200:
            subs = get_resp.json()
            for s in subs:
                print(f"  Existing id={s['id']}  callback={s['callback_url']}")
    else:
        print(f"✗ Failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
