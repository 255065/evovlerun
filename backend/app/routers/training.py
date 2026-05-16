"""Training plan endpoints — generation, retrieval, adaptation."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/training", tags=["training"])

RaceType = Literal["5k", "10k", "half_marathon", "marathon", "ultra", "triathlon"]
Philosophy = Literal[
    "daniels",
    "hansons",
    "pfitzinger",
    "norwegian",
    "polarized",
    "lydiard",
    "auto_hybrid",
]


class PlanRequest(BaseModel):
    race_type: RaceType
    target_time_seconds: int | None = Field(default=None, description="Target finish time in seconds")
    race_date: str = Field(description="ISO date YYYY-MM-DD")
    philosophy: Philosophy = "auto_hybrid"
    current_weekly_km: float | None = None


class PlanSummary(BaseModel):
    plan_id: str
    race_type: RaceType
    race_date: str
    weeks: int
    phase: Literal["base", "build", "peak", "taper", "race"]
    philosophy: Philosophy


@router.post("/plan", response_model=PlanSummary)
def create_plan(
    body: PlanRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PlanSummary:
    """Generate a periodized training plan. Stub — real impl calls Claude with the
    user's performance profile and historical data."""
    # TODO: hand off to plan-generation service (Claude + sports-science RAG)
    return PlanSummary(
        plan_id="stub-plan-id",
        race_type=body.race_type,
        race_date=body.race_date,
        weeks=0,
        phase="base",
        philosophy=body.philosophy,
    )


@router.get("/plan/current", response_model=PlanSummary | None)
def get_current_plan(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PlanSummary | None:
    """Return the user's active plan, or None if they don't have one."""
    # TODO: fetch from training_plans table
    return None
