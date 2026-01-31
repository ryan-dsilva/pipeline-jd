#!/usr/bin/env bash

DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$DIR/.pids"

if [ ! -f "$PIDFILE" ]; then
  echo "No .pids file found. Services may not be running."
  exit 0
fi

while IFS='=' read -r name pid; do
  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name (pid $pid)..."
    kill "$pid" 2>/dev/null
    # Kill child processes (uvicorn spawns workers, npm spawns vite)
    pkill -P "$pid" 2>/dev/null || true
  else
    echo "$name (pid $pid) already stopped."
  fi
done < "$PIDFILE"

rm -f "$PIDFILE"
echo "All services stopped."
