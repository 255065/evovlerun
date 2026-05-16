"""FastAPI entry point for the EvolveRun backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, health, ingestion, training

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("evolverun")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("Starting EvolveRun backend (env=%s)", settings.env)
    yield
    log.info("Shutting down EvolveRun backend")


app = FastAPI(
    title="EvolveRun API",
    description="Adaptive Performance OS — backend for the AI training coach.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes
app.include_router(health.router)

# Authenticated routes
app.include_router(auth.router)
app.include_router(ingestion.router)
app.include_router(training.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "evolverun-backend", "docs": "/docs"}
