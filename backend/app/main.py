"""FastAPI entry point for the EvolveRun backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, health, ingestion, limiter, mcp_keys, metrics, performance, providers, training
from mcp_server.server import build_server as build_mcp_server
from mcp_server.token_verifier import EvolveRunTokenVerifier

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("evolverun")

# Build the MCP server once at import time. We mount its streamable-HTTP app
# under /mcp and hook its task-group lifespan into ours below.
_mcp = build_mcp_server(token_verifier=EvolveRunTokenVerifier())
_mcp_app = _mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log.info("Starting EvolveRun backend (env=%s)", settings.env)
    # The MCP streamable-HTTP app maintains its own session/task-group lifespan
    # that must be activated alongside ours. Without this, mounted MCP requests
    # raise "Task group is not initialized" mid-request.
    async with _mcp_app.router.lifespan_context(_app):
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
app.include_router(limiter.router)
app.include_router(mcp_keys.router)
app.include_router(metrics.router)
app.include_router(performance.router)
app.include_router(providers.router)
app.include_router(training.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "evolverun-backend", "docs": "/docs"}


# Mount MCP server under /mcp. Each MCP request must carry
# `Authorization: Bearer evr_…` — the token verifier resolves it to the same
# user_id we use for REST endpoints. FastMCP exposes a single POST route at
# /mcp (its default path), which after our mount lives at /mcp/mcp.
app.mount("/mcp", _mcp_app)
