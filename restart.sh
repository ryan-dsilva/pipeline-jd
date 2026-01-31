#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$DIR/logs"

# Function to rotate logs for a service (keeps 3 most recent)
rotate_logs() {
  local service=$1

  mkdir -p "$LOGDIR"

  # Rotate backwards to avoid overwriting
  [ -f "$LOGDIR/$service-2.log" ] && mv "$LOGDIR/$service-2.log" "$LOGDIR/$service-3.log"
  [ -f "$LOGDIR/$service-1.log" ] && mv "$LOGDIR/$service-1.log" "$LOGDIR/$service-2.log"
  [ -f "$LOGDIR/$service-current.log" ] && mv "$LOGDIR/$service-current.log" "$LOGDIR/$service-1.log"

  # Clean up old logs (anything numbered 4 and above)
  rm -f "$LOGDIR/$service"-[4-9].log "$LOGDIR/$service"-[0-9][0-9].log
}

echo "=== Restarting services ==="
echo ""

# Step 1: Kill existing services
if [ -f "$DIR/kill.sh" ]; then
  echo "Stopping services..."
  "$DIR/kill.sh"
  echo ""
else
  echo "WARNING: kill.sh not found, skipping stop phase"
  echo ""
fi

# Step 2: Rotate logs
echo "Rotating logs..."
rotate_logs "pocketbase"
rotate_logs "backend"
echo "Logs rotated (keeping 3 most recent per service)"
echo ""

# Step 3: Start services
if [ -f "$DIR/start.sh" ]; then
  echo "Starting services..."
  "$DIR/start.sh"
else
  echo "ERROR: start.sh not found"
  exit 1
fi
