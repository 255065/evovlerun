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


# ----------------------------------------------------------------------------
# OAuth discovery for the MCP connector (RFC 9728)
#
# Claude.ai and other MCP clients look here when a user adds the connector,
# to learn how to authenticate. Without this on the *root* origin (not under
# /mcp), Claude.ai's "Couldn't reach the MCP server" handshake fails before
# it ever sends a tool call.
#
# We're a pure Bearer-token resource server — no real OAuth authorization
# server — so we publish the minimum metadata the spec requires and point at
# our own origin as the (non-)authorization server.
# ----------------------------------------------------------------------------
import os  # noqa: E402

@app.get("/.well-known/oauth-protected-resource", include_in_schema=False)
def oauth_protected_resource() -> dict:
    base = os.environ.get("MCP_PUBLIC_URL", "http://localhost:8000").rstrip("/")
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [base],
        "scopes_supported": ["mcp"],
        "bearer_methods_supported": ["header"],
    }


@app.get("/.well-known/oauth-authorization-server", include_in_schema=False)
def oauth_authorization_server() -> dict:
    """Minimal AS metadata so the client's discovery chain doesn't dead-end.

    We don't run a real authorization server — tokens are issued out-of-band
    via /dashboard/mcp — but Claude.ai will 404-fail the connector if we
    leave this empty. We advertise the resource server URL and bearer-only
    flow so the client knows to skip the authorization dance and just send
    its token.
    """
    base = os.environ.get("MCP_PUBLIC_URL", "http://localhost:8000").rstrip("/")
    return {
        "issuer": base,
        "response_types_supported": [],
        "grant_types_supported": [],
        "token_endpoint_auth_methods_supported": ["bearer"],
        "scopes_supported": ["mcp"],
    }


# Mount MCP server under /mcp. Each MCP request must carry
# `Authorization: Bearer evr_…` — the token verifier resolves it to the same
# user_id we use for REST endpoints. FastMCP exposes a single POST route at
# /mcp (its default path), which after our mount lives at /mcp/mcp.
app.mount("/mcp", _mcp_app)
