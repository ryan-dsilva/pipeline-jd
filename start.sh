#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/.pids"
LOGDIR="$DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGDIR"

# Clean up any stale pidfile
rm -f "$PIDFILE"

# ── PocketBase ────────────────────────────────────────────────────
if [ -x "$DIR/pocketbase/pocketbase" ]; then
  echo "Starting PocketBase..."
  cd "$DIR/pocketbase"
  ./pocketbase serve 2>&1 | tee "$LOGDIR/pocketbase-current.log" &
  echo "pocketbase=$!" >> "$PIDFILE"
else
  echo "WARNING: PocketBase binary not found at pocketbase/pocketbase"
  echo "  Download from https://pocketbase.io/docs/ and place it there."
fi

# ── Backend ───────────────────────────────────────────────────────
echo "Starting backend..."
cd "$DIR/backend"
python3 -m uvicorn app.main:app --reload --port 8000 2>&1 | tee "$LOGDIR/backend-current.log" &
echo "backend=$!" >> "$PIDFILE"

# ── Frontend ──────────────────────────────────────────────────────
echo "Starting frontend..."
cd "$DIR/frontend"
VITE_LOG="$DIR/.vite_output"
npm run dev > "$VITE_LOG" 2>&1 &
echo "frontend=$!" >> "$PIDFILE"

# Wait for Vite to print the port, then open it
VITE_URL=""
for i in $(seq 1 30); do
  if VITE_URL=$(grep -o 'http://localhost:[0-9]*' "$VITE_LOG" 2>/dev/null | head -1) && [ -n "$VITE_URL" ]; then
    break
  fi
  sleep 0.5
done

echo ""
echo "All services started."
echo "  PocketBase admin: http://127.0.0.1:8090/_/"
echo "  Backend API:      http://localhost:8000"
echo "  Frontend:         ${VITE_URL:-http://localhost:5173}"
echo ""
echo "Run ./stop.sh to shut everything down."

open "${VITE_URL:-http://localhost:5173}"

# Stream Vite output so logs are visible
tail -f "$VITE_LOG" &
echo "vite_tail=$!" >> "$PIDFILE"

wait
