# EvolveRun backend — FastAPI + mounted MCP server.
# Single-stage build because the Python deps are pure-Python or have wheels;
# we don't need a separate compile stage. Bumping to multi-stage only buys us
# ~50MB which isn't worth the complexity here.

FROM python:3.13-slim

# Faster, smaller, no .pyc clutter.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# curl is handy for Railway/Render's HTTP healthchecks; tini ensures signals
# (SIGTERM on redeploy) actually reach uvicorn instead of getting swallowed.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl tini \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer the requirements install separately so code changes don't bust the
# wheel cache.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the rest of the backend.
COPY . .

# The hosting platform (Railway/Render/Fly) injects $PORT. Default to 8000
# for local docker runs.
ENV PORT=8000
EXPOSE 8000

# tini PID-1, then uvicorn. We bind 0.0.0.0 because containers route through
# their own network stack — localhost-only won't be reachable from the host.
#
# --proxy-headers + --forwarded-allow-ips="*" make uvicorn trust the
# X-Forwarded-Proto / X-Forwarded-For headers Railway's edge sets. Without
# this, slash-redirects (e.g. /mcp → /mcp/) come back as http://… instead
# of https://… and Claude.ai's connector flow refuses the downgrade.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips=*"]
