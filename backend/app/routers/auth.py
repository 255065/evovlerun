"""Auth-protected endpoint that returns the current user — useful smoke test."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUser)
def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    """Returns the authenticated user. Requires `Authorization: Bearer <supabase-jwt>`."""
    return user
