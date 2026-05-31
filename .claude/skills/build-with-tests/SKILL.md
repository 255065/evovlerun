---
name: build-with-tests
description: How EvolveRun builds — match existing patterns, write tests alongside code, and run the full gate (typecheck, lint, tests) before declaring done. Use when implementing or changing backend or frontend code outside the full feature-factory flow, or any time you want the house build conventions applied.
---

# Build with tests

The EvolveRun way to write code. The builder agents inherit this; use it for
any standalone change too.

## 1. Match before you invent
Read the nearest existing example first and copy its shape:
- Backend route → copy an existing router in `backend/app/routers/`.
- Backend service → copy a service in `backend/app/services/`.
- MCP tool → copy a tool in `backend/mcp_server/tools/` (and remember: NO
  `from __future__ import annotations` in those files).
- Frontend data access → copy the `actions.ts` + page pattern already used in
  the same dashboard area.
- Frontend UI → reuse `components/ui/` primitives, `<Brand/>`, `.evr-*` tokens,
  warm-beige minimalist, English only.

## 2. Tests alongside code, not after
- Backend: pytest in `backend/tests/`, mirroring existing fixtures. Cover the
  happy path + the failure paths (401/403, wrong tenant, empty data).
- Frontend: Vitest + RTL `*.test.tsx` next to the component — render, happy
  path, loading + error states.

## 3. Non-negotiables (from CLAUDE.md)
- RLS / tenant isolation on every user-scoped query.
- No server-side LLM calls in V1.
- Encrypt provider tokens with Fernet; never log secrets.
- Don't add a 12th MCP tool — extend `save-training-plan`.
- Schema change ⇒ a `supabase/migrations/NNNN_*.sql` with its RLS policy
  (applied manually in Supabase, not run by you).

## 4. Run the gate before saying "done"
Backend (from `backend/`):
```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check .   # if ruff is configured
```
Frontend (from `frontend/`):
```bash
npx tsc --noEmit
npm run test        # vitest run
npx next lint       # if quick
```
A change is not done while any gate is red. Errors propagate — don't swallow
them to make a gate pass.

## 5. Report what you touched
List files added/edited, patterns reused, any migration to apply manually, and
any CLAUDE.md rule that would have helped but was missing (so we can add it).
