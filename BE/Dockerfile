# syntax=docker/dockerfile:1
# Production Django images.
#   api    — Gunicorn only (lean)
#   worker — same app + Google Chrome for Twitter/YouTube scraping
#
# Build API:
#   docker build --target api -t kleio-api ./BE
# Build worker:
#   docker build --target worker -t kleio-worker ./BE

FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Do not `pip install --upgrade pip` — keeps build tooling from floating.
RUN python -m venv /opt/venv \
  && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim-bookworm AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=settings \
    PORT=8000

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd --system --gid 1001 app \
  && useradd --system --uid 1001 --gid app --create-home --home-dir /home/app app \
  && mkdir -p /home/app/.local/share /home/app/.cache /tmp/chrome-user-data \
  && chown -R app:app /home/app /tmp/chrome-user-data

ENV HOME=/home/app \
    XDG_CACHE_HOME=/home/app/.cache \
    XDG_CONFIG_HOME=/home/app/.config \
    XDG_DATA_HOME=/home/app/.local/share \
    CHROME_USER_DATA_DIR=/tmp/chrome-user-data

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/api/health" || exit 1

CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]

FROM api AS worker

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
  && wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
  && apt-get install -y --no-install-recommends /tmp/google-chrome.deb \
  && rm -f /tmp/google-chrome.deb \
  && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/google-chrome \
    CHROME_PATH=/usr/bin/google-chrome \
    HOME=/home/app \
    XDG_CACHE_HOME=/home/app/.cache \
    XDG_CONFIG_HOME=/home/app/.config \
    XDG_DATA_HOME=/home/app/.local/share \
    CHROME_USER_DATA_DIR=/tmp/chrome-user-data

# Ensure Chrome/undetected-chromedriver can write under a real home + tmp profile.
RUN mkdir -p /home/app/.local/share /home/app/.cache /tmp/chrome-user-data \
  && chown -R app:app /home/app /tmp/chrome-user-data

USER app

# No HTTP healthcheck — this process is the monitor loop, not an API.
HEALTHCHECK NONE

CMD ["python", "manage.py", "auto_monitor", "start"]
