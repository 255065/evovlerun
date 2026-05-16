"""Health check endpoints — used by load balancers and uptime monitoring."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe. Returns 200 as long as the process is up."""
    return HealthResponse(
        status="ok",
        service="evolverun-backend",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
