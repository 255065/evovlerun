#!/bin/bash
# EvolveRun dev script — starter frontend + backend i parallelt

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Farver
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

# PIDs
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo -e "${YELLOW}🛑 Stopper servere...${RESET}"
  [[ -n "$BACKEND_PID" ]]  && kill "$BACKEND_PID"  2>/dev/null
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  echo -e "${RED}Servere stoppet.${RESET}"
  exit 0
}
trap cleanup SIGINT SIGTERM

# Tjek om port er i brug
port_in_use() { lsof -i TCP:"$1" -sTCP:LISTEN -t &>/dev/null; }

echo ""
echo -e "${GREEN}🚀 EvolveRun dev environment${RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# --- Backend ---
if port_in_use 8000; then
  echo -e "${YELLOW}⚠️  Port 8000 er allerede i brug — springer backend over${RESET}"
else
  echo -e "${CYAN}📦 Backend${RESET}  → http://localhost:8000/docs"
  cd "$BACKEND_DIR"
  .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 2>&1 \
    | sed "s/^/  [backend] /" &
  BACKEND_PID=$!
  sleep 1   # giv FastAPI tid til at starte
fi

# --- Frontend ---
if port_in_use 3000; then
  echo -e "${YELLOW}⚠️  Port 3000 er allerede i brug — springer frontend over${RESET}"
else
  echo -e "${CYAN}⚛️  Frontend${RESET} → http://localhost:3000"
  cd "$FRONTEND_DIR"
  npm run dev 2>&1 \
    | sed "s/^/  [frontend] /" &
  FRONTEND_PID=$!
fi

echo ""
echo -e "${GREEN}✅ Servere kører — tryk Ctrl+C for at stoppe${RESET}"
echo ""

wait
