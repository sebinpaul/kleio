#!/usr/bin/env bash
# Watchdog: ensure Kleio worker is running and can reach MongoDB.
# On failure → restart worker. Optionally ping Healthchecks.io.
#
# Cron (every 5 min):
#   */5 * * * * /opt/kleio/scripts/worker-watchdog.sh >> /var/log/kleio-worker-watchdog.log 2>&1
#
# Optional in /opt/kleio/.env (not committed):
#   HEALTHCHECKS_PING_URL=https://hc-ping.com/YOUR-UUID
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

HEALTHCHECKS_PING_URL="${HEALTHCHECKS_PING_URL:-}"
if [[ -z "$HEALTHCHECKS_PING_URL" && -f "$ROOT/.env" ]]; then
  HEALTHCHECKS_PING_URL="$(grep -E '^HEALTHCHECKS_PING_URL=' "$ROOT/.env" | tail -n1 | cut -d= -f2- | tr -d '"' | tr -d "'" || true)"
fi

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

worker_running() {
  docker compose ps --status running --services 2>/dev/null | grep -qx worker
}

mongo_ok() {
  docker compose exec -T worker python - <<'PY' >/dev/null 2>&1
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
import django
django.setup()
from mongoengine.connection import get_db
get_db().command("ping")
print("ok")
PY
}

recent_mongo_errors() {
  # Only look at the last 10 minutes so old log lines don't force endless restarts
  docker compose logs worker --since 10m 2>/dev/null \
    | grep -Eqi 'Temporary failure in name resolution|Name or service not known|AutoReconnect|ServerSelectionTimeoutError'
}

restart_worker() {
  log "Restarting worker..."
  docker compose up -d worker
  sleep 8
}

ping_ok() {
  local url="${HEALTHCHECKS_PING_URL:-}"
  [[ -n "$url" ]] || return 0
  curl -fsS -o /dev/null --connect-timeout 5 --max-time 10 "$url" || log "WARN: Healthchecks success ping failed"
}

ping_fail() {
  local url="${HEALTHCHECKS_PING_URL:-}"
  [[ -n "$url" ]] || return 0
  curl -fsS -o /dev/null --connect-timeout 5 --max-time 10 "${url}/fail" || log "WARN: Healthchecks fail ping failed"
}

healthy=0

if ! worker_running; then
  log "Worker container not running"
  restart_worker
fi

if worker_running && mongo_ok; then
  if recent_mongo_errors; then
    # Process may be limping after a DNS blip even if a one-shot ping works
    log "Worker ping OK but recent Mongo/DNS errors in logs — restarting to clear stuck state"
    restart_worker
    if worker_running && mongo_ok; then
      healthy=1
    fi
  else
    healthy=1
  fi
else
  log "Worker unhealthy (down or Mongo unreachable) — restarting"
  restart_worker
  if worker_running && mongo_ok; then
    healthy=1
  fi
fi

if [[ "$healthy" -eq 1 ]]; then
  log "Worker healthy"
  ping_ok
  exit 0
fi

log "Worker still unhealthy after restart"
ping_fail
exit 1
