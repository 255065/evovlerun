# Deploy EvolveRun's backend (Phase B)

The backend serves both the REST API **and** the MCP server at `/mcp/mcp`.
Single container, single port. Once it's reachable on a public HTTPS URL,
users add it to Claude.ai's "custom connectors" exactly like they would
Chirona — no Anthropic marketplace listing required.

## Option 1 — Railway (recommended, fastest)

1. **Push the repo to GitHub** (already done).
2. **Create a Railway project** → "Deploy from GitHub repo" → pick `255065/evovlerun`.
3. **Set the root directory** to `backend/`. Railway will pick up our
   `Dockerfile` and `railway.toml` automatically.
4. **Add environment variables** (Settings → Variables):

   | Variable | Value |
   |---|---|
   | `ENV` | `production` |
   | `LOG_LEVEL` | `INFO` |
   | `CORS_ORIGINS` | `https://your-frontend.vercel.app,https://claude.ai` |
   | `SUPABASE_URL` | from Supabase Settings → API |
   | `SUPABASE_ANON_KEY` | from Supabase Settings → API |
   | `SUPABASE_SERVICE_ROLE_KEY` | from Supabase Settings → API (server-only!) |
   | `SUPABASE_JWT_SECRET` | from Supabase Settings → JWT |
   | `TOKEN_ENCRYPTION_KEY` | from your local `.env` (Fernet key) |
   | `OAUTH_STATE_SECRET` | from your local `.env` |
   | `MINIMAX_API_KEY` | your MiniMax API key |
   | `MINIMAX_BASE_URL` | `https://api.minimax.io/v1` |
   | `LLM_PROVIDER` | `minimax` |
   | `MCP_PUBLIC_URL` | the public URL Railway gives you (set after first deploy) |
   | `FRONTEND_URL` | your frontend's public URL |
   | `BACKEND_PUBLIC_URL` | the public URL Railway gives you |
   | OAuth provider secrets | `STRAVA_*`, `GARMIN_*`, etc. as needed |

5. **First deploy** — Railway builds the Docker image, runs it, hits `/health`
   for the readiness probe, and assigns a public URL like
   `evolverun-backend-production.up.railway.app`.

6. **Update `MCP_PUBLIC_URL`** to point at that URL and redeploy. The MCP
   issuer URL needs to match the actual hostname so Claude trusts the
   auth flow.

7. **Optional: custom domain**. In Railway → Settings → Domains, add
   e.g. `mcp.evolverun.app`. CNAME the DNS record to Railway's target and
   wait for the TLS cert to issue (~minutes).

## Option 2 — Render

Almost identical. Set the same env vars, point at `backend/` as the root,
let Render auto-detect the Dockerfile. Render's free tier sleeps after
15 minutes of inactivity — Railway doesn't, which matters for an MCP server.

## Verifying the deploy

```bash
# Liveness
curl https://your-public-url/health

# MCP handshake with a real API key (generate one in /dashboard/mcp first)
curl -X POST https://your-public-url/mcp/mcp \
  -H "Authorization: Bearer evr_…" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

A valid response is an SSE stream starting with `event: message` followed
by the EvolveRun server capabilities.

## Adding to Claude.ai (end-user flow)

Once the backend is live:

1. Open Claude.ai → Settings → Connectors → **Add custom connector**
2. URL: `https://your-public-url/mcp/mcp`
3. Auth: paste an EvolveRun API key from `/dashboard/mcp`
4. Save. The 20 EvolveRun tools become available in any new Claude chat.

This is the same flow Chirona uses — no marketplace, no review process.

## Frontend (Vercel)

Deploy the `frontend/` directory to Vercel separately. It only needs:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | your Railway backend URL |
| `NEXT_PUBLIC_SUPABASE_URL` | same as backend |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | same as backend |

That's it for the public site.
