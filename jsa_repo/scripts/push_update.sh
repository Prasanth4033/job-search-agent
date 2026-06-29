#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# push_update.sh
# Commit all local changes and push to GitHub (origin/main).
#
# Usage:
#   ./scripts/push_update.sh                              # auto commit message
#   ./scripts/push_update.sh "feat: add Robert Half"     # custom commit message
#
# Common workflows:
#   # After editing sources.json to add a new agency:
#   ./scripts/push_update.sh "feat: add Robert Half as a new source"
#
#   # After editing sources.json to disable an agency:
#   ./scripts/push_update.sh "chore: disable ABC Consultants"
#
#   # After updating skills in config.yaml:
#   ./scripts/push_update.sh "config: update skill keywords"
#
# Prerequisites:
#   - git remote "origin" must point to your GitHub repo
#   - Either SSH keys are configured, OR set GITHUB_TOKEN in .env
#     GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# ── Load GitHub token from .env if present ────────────────────────────────────
if [ -f ".env" ]; then
  export $(grep -E '^GITHUB_TOKEN=' .env | xargs) 2>/dev/null || true
fi

# ── Validate git repo ─────────────────────────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "ERROR: Not a git repository. Run 'git init' first."
  exit 1
fi

# ── Check for uncommitted changes ─────────────────────────────────────────────
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  echo "Nothing to commit — working tree is clean."
  exit 0
fi

# ── Build commit message ──────────────────────────────────────────────────────
TIMESTAMP="$(date -u '+%Y-%m-%d %H:%M UTC')"

if [ -n "${1:-}" ]; then
  COMMIT_MSG="$1"
else
  # Auto-detect what changed
  CHANGED_FILES="$(git status --short | awk '{print $2}' | tr '\n' ', ' | sed 's/,$//')"

  if git diff --name-only HEAD 2>/dev/null | grep -q "sources.json"; then
    COMMIT_MSG="chore: update sources.json — $TIMESTAMP"
  elif git diff --name-only HEAD 2>/dev/null | grep -q "config"; then
    COMMIT_MSG="chore: update config — $TIMESTAMP"
  else
    COMMIT_MSG="chore: update project files — $TIMESTAMP"
  fi
fi

# ── Stage all changes ─────────────────────────────────────────────────────────
echo "==> Staging changes..."
git add -A

echo "==> Changed files:"
git diff --cached --name-only | sed 's/^/    /'

# ── Commit ────────────────────────────────────────────────────────────────────
echo ""
echo "==> Committing: \"$COMMIT_MSG\""
git commit -m "$COMMIT_MSG"

# ── Set remote URL with token if GITHUB_TOKEN is available ───────────────────
CURRENT_REMOTE="$(git remote get-url origin 2>/dev/null || echo '')"

if [ -n "${GITHUB_TOKEN:-}" ]; then
  # Extract owner/repo from existing remote URL
  REPO_PATH="$(echo "$CURRENT_REMOTE" | sed -E 's|https?://([^@]+@)?github.com/||; s|\.git$||')"
  if [ -n "$REPO_PATH" ]; then
    git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${REPO_PATH}.git"
  fi
fi

# ── Push ──────────────────────────────────────────────────────────────────────
echo "==> Pushing to origin/main..."
git push origin main

# ── Restore remote URL (strip token) ─────────────────────────────────────────
if [ -n "${GITHUB_TOKEN:-}" ] && [ -n "$REPO_PATH" ]; then
  git remote set-url origin "https://github.com/${REPO_PATH}.git"
fi

echo ""
echo "✓ Done! Changes pushed to GitHub."
echo "  Repo: $(git remote get-url origin)"
echo "  Commit: $(git log -1 --oneline)"
