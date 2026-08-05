# Kleio deployment guide (no domain yet — IP / localhost)

This repo deploys as **3 Docker services**: `api`, `worker` (Chrome), `ui`.
Best fit: a **Linux x86_64 VM** (2+ vCPU, **4GB+ RAM**) with Docker + Compose.

HTTPS / custom domain is **deferred** until you have a domain. Until then use
`http://SERVER_IP:3000` (UI) and `http://SERVER_IP:8000` (API).

**Hetzner (recommended):** follow **[DEPLOYMENT.hetzner.md](./DEPLOYMENT.hetzner.md)** for the full step-by-step.

---

## Architecture

```
Browser  →  :3000  ui (Next.js)
         →  :8000  api (Django/Gunicorn)
                    │
                    └─ MongoDB Atlas (external)
Worker   →  Chrome scrapers (Twitter/YouTube) + Reddit/HN APIs
```

| Service | Image target | Needs |
|---------|--------------|--------|
| api | `BE` `--target api` | MongoDB, Clerk, Reddit, Resend env |
| worker | `BE` `--target worker` | Same env + Chrome (~2GB shm) |
| ui | `UI` Dockerfile | Build args for `NEXT_PUBLIC_*` + runtime `CLERK_SECRET_KEY` |

---

## Pre-deploy checklist (do these before first prod boot)

### 1. Host requirements
- [ ] Ubuntu 22.04+ (or similar), **amd64** (Chrome `.deb` is amd64)
- [ ] Docker Engine + Compose plugin installed
- [ ] Open firewall ports **3000** and **8000** (or put a proxy later)
- [ ] **4GB RAM minimum** (worker + Chrome will OOM on 1GB)

> **Firewall note:** Ports 3000 and 8000 must be public. Use your cloud provider's edge firewall (e.g. Hetzner Cloud Firewall) to control access. Don't rely on `ufw` for these — Docker bypasses ufw for published ports, so `ufw allow 3000` won't actually restrict anything. Until you add HTTPS, these ports serve plain HTTP to the world; the API is protected by Clerk JWT on keyword/mention endpoints.

### 2. External services
- [ ] MongoDB Atlas cluster + connection string (allow server IP in Atlas Network Access)
- [ ] Clerk app: add `http://SERVER_IP:3000` to allowed origins / redirect URLs
- [ ] Reddit app credentials
- [ ] Resend API key + from-address

### 3. Secrets / env files on the server
Copy examples and fill real values (never commit):

```bash
cp .env.example .env
cp BE/.env.example BE/.env
```

**Root `.env`** (UI build + UI Clerk secret):

| Variable | Example (no domain) |
|----------|---------------------|
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `pk_live_...` or `pk_test_...` |
| `CLERK_SECRET_KEY` | `sk_...` |
| `NEXT_PUBLIC_API_URL` | `http://SERVER_IP:8000` |
| `NEXT_PUBLIC_SITE_URL` | `http://SERVER_IP:3000` |

**`BE/.env`** (API + worker):

| Variable | Production (no domain) |
|----------|------------------------|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | long random secret |
| `ALLOWED_HOSTS` | `SERVER_IP,localhost` |
| `SECURE_SSL_REDIRECT` | `False` (no TLS yet) |
| `USE_X_FORWARDED_HOST` | `False` |
| `CORS_ALLOWED_ORIGINS` | `http://SERVER_IP:3000` |
| `CLERK_AUTHORIZED_PARTIES` | `http://SERVER_IP:3000` |
| `MONGODB_URI` / `MONGODB_DATABASE` | Atlas URI |
| Reddit / Resend / Clerk | real values |
| `CLERK_JWT_KEY` | single-line PEM with `\n` if used |

Replace `SERVER_IP` with the VM public IP (or `localhost` for local prod-like test).

### 4. Rebuild UI when IP/URL changes
`NEXT_PUBLIC_*` is baked at **image build**. If the IP changes, rebuild UI:

```bash
docker compose build --no-cache ui
docker compose up -d ui
```

---

## Deploy commands

On the server (repo root):

```bash
# 1. Fill .env and BE/.env (see above)

# 2. Build + start all services
docker compose up --build -d

# 3. Smoke check
./scripts/smoke-check.sh
# or:
curl -fsS http://localhost:8000/api/health
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:3000
docker compose ps
docker compose logs -f worker --tail 50
```

Useful:

```bash
docker compose ps
docker compose logs -f api worker ui
docker compose restart worker
docker compose down
```

---

## Post-boot verification

- [ ] `GET http://SERVER_IP:8000/api/health` → `{"status":"ok"}`
- [ ] `http://SERVER_IP:3000` loads landing page
- [ ] Sign-in / Clerk works (origins configured for that IP)
- [ ] Create a Reddit or HN keyword → worker logs show monitoring
- [ ] Twitter/YouTube keyword → worker can start Chrome (check logs for driver errors)

---

## Known limitations (until domain + HTTPS)

1. **No TLS** — traffic to 3000/8000 is plain HTTP. The API keyword/mention endpoints are protected by Clerk JWT; everything else (`/api/health`, the UI) is public. Fine for personal/staging use — be deliberate about it.
2. **Clerk + IP** — some Clerk features prefer real domains; test sign-in early.
3. **UI rebuild required** when IP changes.
4. **Scraping fragility** — Twitter/YouTube via Chrome can break if sites block the server IP.
5. **No reverse proxy yet** — ports 3000/8000 exposed directly.
6. **No `migrate` step** — the SQLite DB (`db.sqlite3`) is created lazily; Django's auth/admin tables aren't migrated. Core app works because data is MongoEngine, but `/admin` and any ORM-backed path will break. Run `docker compose exec api python manage.py migrate` if you need them.

---

## When you get a domain (later)

1. Point DNS A record → server IP  
2. Add Caddy/Nginx for `:443` → ui / `/api` → api  
3. Set `SECURE_SSL_REDIRECT=True`, `USE_X_FORWARDED_HOST=True`  
4. Rebuild UI with `https://your.domain` URLs  
5. Update Clerk / CORS / `ALLOWED_HOSTS`

---

## Rollback

```bash
docker compose down
# optionally remove images
docker image rm kleio-api:local kleio-worker:local
```
