#!/bin/bash

# Unified test runner for backend and frontend tests
# Runs tests sequentially and logs output to test-runs/ directory

set -e

# Create test-runs directory if it doesn't exist
mkdir -p test-runs

# Generate timestamp for log file (yyyy-mm-dd-hh-mm)
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
LOG_FILE="test-runs/${TIMESTAMP}.log"

echo "==================================================" | tee "$LOG_FILE"
echo "Test Run Started: $(date)" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run backend tests
echo ">>> Running Backend Tests (pytest)..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
cd backend
if [ "$1" = "paid" ]; then
    echo ">>> Including PAID tests (Anthropic API calls)" | tee -a "../$LOG_FILE"
    python -m pytest tests/ -v 2>&1 | tee -a "../$LOG_FILE"
else
    echo ">>> Excluding paid tests (use './run-tests.sh paid' to include)" | tee -a "../$LOG_FILE"
    python -m pytest tests/ -v -m "not anthropic_api" 2>&1 | tee -a "../$LOG_FILE"
fi
BACKEND_EXIT=$?
cd ..
echo "" | tee -a "$LOG_FILE"

if [ $BACKEND_EXIT -eq 0 ]; then
    echo "✓ Backend tests passed" | tee -a "$LOG_FILE"
else
    echo "✗ Backend tests failed (exit code: $BACKEND_EXIT)" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "--------------------------------------------------" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run frontend tests
echo ">>> Running Frontend Tests (vitest)..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
cd frontend
npx vitest run 2>&1 | tee -a "../$LOG_FILE"
FRONTEND_EXIT=$?
cd ..
echo "" | tee -a "$LOG_FILE"

if [ $FRONTEND_EXIT -eq 0 ]; then
    echo "✓ Frontend tests passed" | tee -a "$LOG_FILE"
else
    echo "✗ Frontend tests failed (exit code: $FRONTEND_EXIT)" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"
echo "Test Run Completed: $(date)" | tee -a "$LOG_FILE"
echo "==================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Exit with failure if either test suite failed
if [ $BACKEND_EXIT -ne 0 ] || [ $FRONTEND_EXIT -ne 0 ]; then
    exit 1
fi

exit 0
