#!/usr/bin/env bash
# =============================================================================
# setup.sh  —  Run this ONCE to create the GitHub repo and push everything.
# After that, GitHub Actions takes over automatically every day. Forever.
#
# Requirements: git + GitHub CLI (gh)
#   macOS:   brew install gh && gh auth login
#   Linux:   https://cli.github.com/manual/installation
#   Windows: winget install GitHub.cli
# =============================================================================

set -e

REPO_NAME="daily-pulse"
REPO_DESC="🌍 Auto-updated daily data: NASA APOD, crypto prices, trending repos, quotes & fun facts"

echo "════════════════════════════════════════════"
echo "  Daily Pulse — one-time GitHub setup"
echo "════════════════════════════════════════════"
echo ""

# Verify gh is installed
if ! command -v gh &>/dev/null; then
  echo "❌  GitHub CLI (gh) is not installed."
  echo "    Install it from: https://cli.github.com"
  exit 1
fi

# Verify authenticated
if ! gh auth status &>/dev/null; then
  echo "❌  Not logged in to GitHub CLI."
  echo "    Run: gh auth login"
  exit 1
fi

echo "✅  GitHub CLI ready"
echo ""

# Create the repo on GitHub
echo "📦  Creating GitHub repo: $REPO_NAME ..."
gh repo create "$REPO_NAME" \
  --public \
  --description "$REPO_DESC" \
  --confirm 2>/dev/null && echo "    Repo created!" || echo "    (Repo may already exist, continuing...)"

echo ""

# Init git if not already
if [ ! -d ".git" ]; then
  git init
  git branch -M main
fi

# Set remote
GITHUB_USER=$(gh api user -q .login)
REMOTE="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

# Initial commit
git add -A
git commit -m "chore: initial repo setup

- GitHub Actions workflow (runs daily at 07:00 UTC)
- Data fetcher script (NASA APOD, crypto, GitHub trends, quotes, fun facts)
- Auto-updates README.md with latest snapshot
- Stores daily JSON snapshots in data/" 2>/dev/null || echo "(nothing new to commit)"

# Push
echo ""
echo "⬆️   Pushing to GitHub..."
git push -u origin main

echo ""
echo "════════════════════════════════════════════"
echo "  ✅  All done! Setup complete."
echo ""
echo "  Your repo: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "  👉 To trigger the first commit NOW:"
echo "     Go to Actions tab → 'Daily Pulse' → 'Run workflow'"
echo ""
echo "  After that, it runs automatically every day at 07:00 UTC."
echo "  You never need to touch it again. 🎉"
echo "════════════════════════════════════════════"
