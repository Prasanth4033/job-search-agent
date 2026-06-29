#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run.sh — Convenience wrapper for the Job Search Agent
# Usage:
#   ./scripts/run.sh               # single run, 24-hour window, email on
#   ./scripts/run.sh --no-email    # single run, no email
#   ./scripts/run.sh --hours 48    # single run, 48-hour window
#   ./scripts/run.sh --daemon      # daemon mode (daily at 07:00 UTC)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

echo "==> Starting Job Search Agent at $(date -u '+%Y-%m-%d %H:%M UTC')"
python -m job_agent.main "$@"
