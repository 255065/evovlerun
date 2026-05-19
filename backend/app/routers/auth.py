"""Auth-protected endpoints for the current user."""

import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.core.security import CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin

log = logging.getLogger("evolverun.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUser)
def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    """Returns the authenticated user. Requires `Authorization: Bearer <supabase-jwt>`."""
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Hard-delete the current user.

    Cancels any active Stripe subscription, then deletes the user from
    Supabase auth — which cascades to `profiles` and every user-scoped
    table (workouts, daily_metrics, oauth_connections, etc.). The Stripe
    Customer object is intentionally kept so we retain billing history
    for tax / audit purposes.

    Errors at the Stripe step are logged but don't block the auth delete:
    a user who can no longer log in matters more than a tidy Stripe state
    we can clean up manually later.
    """
    supabase = get_supabase_admin()

    # Pull the profile row so we know what subscription to cancel.
    profile_row = (
        supabase.table("profiles")
        .select("stripe_subscription_id")
        .eq("id", user.id)
        .single()
        .execute()
    )
    sub_id = (profile_row.data or {}).get("stripe_subscription_id")

    if sub_id and settings.stripe_secret_key:
        try:
            stripe.api_key = settings.stripe_secret_key
            stripe.Subscription.cancel(sub_id)
            log.info("Cancelled subscription %s for user %s on delete", sub_id, user.id)
        except stripe.StripeError as exc:
            # Could be already-cancelled, customer-deleted, etc. Log and
            # continue — Stripe state never blocks identity deletion.
            log.warning("Stripe cancel failed during user delete (%s): %s", sub_id, exc)

    # Service-role delete from auth.users. RLS does not apply to admin
    # clients, and the foreign-key cascade in migration 0001 takes care of
    # every user-scoped row in our schema.
    try:
        supabase.auth.admin.delete_user(user.id)
    except Exception as exc:
        log.exception("Failed to delete auth user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not delete user: {exc}",
        ) from exc
