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

echo "==> Rebuilding and restarting containers"
docker compose up --build -d

echo "==> Smoke check"
./scripts/smoke-check.sh

echo "==> Deploy finished"
docker compose ps
