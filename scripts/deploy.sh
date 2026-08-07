#!/usr/bin/env bash
# Deploy Kleio on the VPS (pull latest main + rebuild containers).
# Used by GitHub Actions CD and safe to run manually:
#   cd /opt/kleio && ./scripts/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Pulling latest main"
git fetch origin main
git checkout main
git pull --ff-only origin main

echo "==> Ensuring scripts are executable"
chmod +x scripts/*.sh

echo "==> Rebuilding and restarting containers"
docker compose up --build -d

echo "==> Smoke check"
./scripts/smoke-check.sh

echo "==> Ensuring worker watchdog cron (every 5 min)"
# Idempotent: add the line only if missing. Does not touch Healthchecks URL (set in .env once).
CRON_LINE='*/5 * * * * /opt/kleio/scripts/worker-watchdog.sh >> /var/log/kleio-worker-watchdog.log 2>&1'
if crontab -l 2>/dev/null | grep -Fq "worker-watchdog.sh"; then
  echo "   cron already installed"
else
  (crontab -l 2>/dev/null || true; echo "$CRON_LINE") | crontab -
  echo "   cron installed"
fi

echo "==> Deploy finished"
docker compose ps
