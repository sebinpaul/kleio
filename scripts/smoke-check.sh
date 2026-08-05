#!/usr/bin/env bash
# Smoke-check local/VM Docker deploy (no domain required).
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
UI_URL="${UI_URL:-http://127.0.0.1:3000}"

echo "==> API health: ${API_URL}/api/health"
curl -fsS "${API_URL}/api/health"
echo

echo "==> UI: ${UI_URL}"
code="$(curl -fsS -o /dev/null -w "%{http_code}" "${UI_URL}" || true)"
if [[ "${code}" != "200" && "${code}" != "307" && "${code}" != "308" && "${code}" != "302" ]]; then
  echo "UI check failed (HTTP ${code:-none})"
  exit 1
fi
echo "UI OK (HTTP ${code})"

if command -v docker >/dev/null 2>&1; then
  echo "==> Compose status"
  docker compose ps || true
fi

echo "Smoke check passed."
