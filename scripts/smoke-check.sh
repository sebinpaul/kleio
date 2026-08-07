#!/usr/bin/env bash
# Smoke-check local/VM Docker deploy (no domain required).
# Retries briefly — UI/API often need a few seconds after container start.
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
UI_URL="${UI_URL:-http://127.0.0.1:3000}"
RETRIES="${SMOKE_RETRIES:-30}"
SLEEP_SECS="${SMOKE_SLEEP_SECS:-2}"

wait_for_http() {
  local name="$1"
  local url="$2"
  local i code

  echo "==> ${name}: ${url}"
  for i in $(seq 1 "${RETRIES}"); do
    code="$(curl -fsS -o /dev/null -w "%{http_code}" --connect-timeout 2 --max-time 5 "${url}" 2>/dev/null || true)"
    if [[ "${code}" == "200" || "${code}" == "307" || "${code}" == "308" || "${code}" == "302" ]]; then
      echo "${name} OK (HTTP ${code}) after ${i} attempt(s)"
      return 0
    fi
    echo "  attempt ${i}/${RETRIES}: HTTP ${code:-000} — waiting ${SLEEP_SECS}s..."
    sleep "${SLEEP_SECS}"
  done

  echo "${name} check failed after ${RETRIES} attempts (last HTTP ${code:-000})"
  return 1
}

echo "==> API health: ${API_URL}/api/health"
api_ok=0
for i in $(seq 1 "${RETRIES}"); do
  if curl -fsS --connect-timeout 2 --max-time 5 "${API_URL}/api/health" >/dev/null 2>&1; then
    curl -fsS "${API_URL}/api/health"
    echo
    echo "API OK after ${i} attempt(s)"
    api_ok=1
    break
  fi
  echo "  attempt ${i}/${RETRIES}: API not ready — waiting ${SLEEP_SECS}s..."
  sleep "${SLEEP_SECS}"
done
if [[ "${api_ok}" -ne 1 ]]; then
  echo "API health check failed"
  exit 1
fi

wait_for_http "UI" "${UI_URL}"

if command -v docker >/dev/null 2>&1; then
  echo "==> Compose status"
  docker compose ps || true
fi

echo "Smoke check passed."
