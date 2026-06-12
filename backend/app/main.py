"""FastAPI entry point for the EvolveRun backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, billing, health, ingestion, mcp_keys, metrics, oauth, performance, providers, training
from mcp_server.server import build_server as build_mcp_server
from mcp_server.token_verifier import EvolveRunTokenVerifier

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("evolverun")

# Error monitoring. No-op unless SENTRY_DSN is set, so dev/test are unaffected.
# Initialise before the app is built so import-time and request errors are both
# captured. The FastAPI integration auto-instruments routes and unhandled
# exceptions; send_default_pii stays False so we never ship user data.
if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )
    log.info("Sentry error monitoring enabled (env=%s)", settings.env)

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
app.include_router(billing.router)
app.include_router(ingestion.router)
app.include_router(mcp_keys.router)
app.include_router(metrics.router)
app.include_router(oauth.router)
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

# The issuer MUST be byte-identical to what FastMCP advertises in its own
# /mcp/.well-known/oauth-protected-resource (which the 401 WWW-Authenticate
# header points strict clients to). FastMCP runs MCP_PUBLIC_URL through
# pydantic AnyHttpUrl, which normalises it to a trailing slash. ChatGPT
# validates that the auth-server `issuer` exactly equals the discovered
# authorization_servers entry — a one-character slash mismatch makes it fail
# with "something went wrong". Claude normalises and tolerates the mismatch,
# which is why it worked while ChatGPT didn't. So we publish the same
# trailing-slash issuer everywhere.
def _mcp_issuer() -> str:
    return os.environ.get("MCP_PUBLIC_URL", "http://localhost:8000").rstrip("/") + "/"


@app.get("/.well-known/oauth-protected-resource", include_in_schema=False)
def oauth_protected_resource() -> dict:
    issuer = _mcp_issuer()
    base = issuer.rstrip("/")
    return {
        "resource": f"{base}/mcp",
        "authorization_servers": [issuer],
        "scopes_supported": ["mcp"],
        "bearer_methods_supported": ["header"],
    }


@app.get("/.well-known/oauth-authorization-server", include_in_schema=False)
def oauth_authorization_server() -> dict:
    """Full authorization-server metadata for OAuth 2.1 + PKCE + DCR.

    Claude.ai and ChatGPT read this to discover where to register, authorize,
    and exchange codes. Order matters — leaving any of these fields off makes
    the discovery probe fail and the user sees "Couldn't reach the MCP
    server" in the UI. The `issuer` carries a trailing slash to match
    FastMCP's normalised advertisement (see _mcp_issuer above).
    """
    issuer = _mcp_issuer()
    base = issuer.rstrip("/")
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "scopes_supported": ["mcp"],
    }


# Mount MCP server under /mcp. Each MCP request must carry
# `Authorization: Bearer evr_…` — the token verifier resolves it to the same
# user_id we use for REST endpoints. FastMCP exposes a single POST route at
# /mcp (its default path), which after our mount lives at /mcp/mcp.
app.mount("/mcp", _mcp_app)
