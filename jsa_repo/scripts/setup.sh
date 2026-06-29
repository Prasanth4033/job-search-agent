#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — One-time environment setup for the Job Search Agent
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==> Setting up Job Search Agent..."

# 1 — Python version check
python3 --version || { echo "ERROR: Python 3 is required."; exit 1; }

# 2 — Create virtual environment
if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# 3 — Install dependencies
echo "==> Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4 — Config setup
if [ ! -f "config.yaml" ]; then
  cp config.example.yaml config.yaml
  echo "==> Created config.yaml from template. Edit it before running the agent."
fi
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "==> Created .env from template. Add your Gmail App Password before running."
fi

# 5 — Create runtime directories
mkdir -p logs reports

# 6 — Make scripts executable
chmod +x scripts/run.sh scripts/setup.sh

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml  — review schedule time, sources, skills."
echo "  2. Edit .env         — set EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT."
echo "  3. Run:  ./scripts/run.sh"
echo "  4. Daemon mode:  ./scripts/run.sh --daemon"
