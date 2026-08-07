# Deploy Kleio on Hetzner (step-by-step)

No domain yet. You will use the server’s **public IP**:

- UI → `http://SERVER_IP:3000`
- API → `http://SERVER_IP:8000`

GitHub repo: `sebinpaul/kleio` (adjust if your remote differs).

---

## 0. Before you start (local checklist)

- [ ] Repo builds locally: `docker compose up --build` works on your Mac
- [ ] MongoDB Atlas cluster ready
- [ ] Clerk, Reddit, Resend keys ready
- [ ] You can SSH with a key pair

---

## 1. Create the Hetzner server

1. Sign up / log in: [https://console.hetzner.cloud](https://console.hetzner.cloud)
2. **New project** → **Add Server**
3. Choose:
   - **Location:** closest to you / users (e.g. Nuremberg, Helsinki, Ashburn if available)
   - **Image:** **Ubuntu 24.04** (or 22.04)
   - **Type:** **CX22** or similar — **2 vCPU / 4 GB RAM** minimum  
     (use **8 GB** if Twitter/YouTube scrapes heavily)
   - **Architecture:** **x86 (Intel/AMD)** — **not ARM** (Chrome `.deb` is amd64)
   - **Networking:** public IPv4 on
   - **SSH key:** add your public key (`~/.ssh/id_ed25519.pub` or similar)
4. Create → note the **public IPv4** → call it `SERVER_IP`

---

## 2. First SSH login

From your Mac:

```bash
ssh root@SERVER_IP
```

(If Hetzner gave you a password once, change it or rely on SSH keys only.)

Optional hardening (recommended):

```bash
apt update && apt upgrade -y
# create a non-root user later if you want; root is fine for first deploy
```

---

## 3. Install Docker + Compose

On the server (as root):

```bash
apt update && apt upgrade -y
apt install -y ca-certificates curl git

# Docker official install
curl -fsSL https://get.docker.com | sh

# Verify
docker --version
docker compose version
```

Enable Docker on boot:

```bash
systemctl enable docker
systemctl start docker
```

---

## 4. Open firewall ports

Your UI (3000) and API (8000) must be **public** — that's the point of the app. Use the Hetzner Cloud Firewall to control who can reach them. Avoid `ufw` for these ports: Docker bypasses ufw for published ports, so `ufw allow 3000` has no effect — 3000 is open to the world regardless.

### Hetzner Cloud Firewall (recommended)

1. **Firewalls** → create firewall
2. Inbound rules:
   - TCP **22** (SSH) — restrict to your IP if possible
   - TCP **3000** (UI) — public
   - TCP **8000** (API) — public
3. Apply firewall to your server

> **Note on security without a domain:** Until you add HTTPS (see "When you get a domain"), traffic to 3000 and 8000 is plain HTTP. The API is protected by Clerk JWT on keyword/mention endpoints, but `/api/health` and the UI are fully public. This is fine for a personal/staging deploy — just be deliberate about it. A reverse proxy + TLS (Caddy/Nginx) closes this gap later.

---

## 5. Clone the repo

```bash
mkdir -p /opt && cd /opt
git clone git@github.com:sebinpaul/kleio.git
# or HTTPS:
# git clone https://github.com/sebinpaul/kleio.git
cd kleio
```

If SSH to GitHub fails from the server, either:

- add a deploy key on GitHub, or  
- use HTTPS + personal access token, or  
- `scp` / `rsync` the project from your laptop.

---

## 6. Configure environment files

Still on the server:

```bash
cd /opt/kleio
cp .env.example .env
cp BE/.env.example BE/.env
nano .env      # or vim
nano BE/.env
```

### Root `.env` (UI build + Clerk secret)

Replace `SERVER_IP` with your real IP:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
NEXT_PUBLIC_API_URL=http://SERVER_IP:8000
NEXT_PUBLIC_SITE_URL=http://SERVER_IP:3000
```

### `BE/.env` (API + worker)

```env
DEBUG=False
DJANGO_SECRET_KEY=<long-random-secret>
ALLOWED_HOSTS=SERVER_IP,localhost,127.0.0.1

SECURE_SSL_REDIRECT=False
USE_X_FORWARDED_HOST=False

MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=kleio

CLERK_SECRET_KEY=sk_...
CLERK_AUTHORIZED_PARTIES=http://SERVER_IP:3000
CORS_ALLOWED_ORIGINS=http://SERVER_IP:3000

REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=KleioMentionTracker/1.0

RESEND_API_KEY=...
RESEND_FROM_EMAIL=...
```

Generate a Django secret (on the server or Mac):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

If you use `CLERK_JWT_KEY`, keep it **one line** with `\n` escapes (see `BE/.env.example`).

---

## 7. Allow the server in MongoDB Atlas + Clerk

### Atlas

1. Atlas → **Network Access** → **Add IP Address**
2. Add `SERVER_IP` (or temporarily `0.0.0.0/0` for testing only)
3. Confirm DB user/password match `MONGODB_URI`

### Clerk

1. Clerk Dashboard → your app
2. Add `http://SERVER_IP:3000` to:
   - allowed origins / redirect URLs / authorized parties (as applicable)
3. Use the same publishable + secret keys as in `.env`

---

## 8. Build and start

On the server:

```bash
cd /opt/kleio
docker compose up --build -d
```

First build takes a while (especially **worker** with Chrome).

Watch progress:

```bash
docker compose ps
docker compose logs -f
```

Expect:

- `api` → healthy  
- `worker` → running (not restart loop)  
- `ui` → running  

Apply Django migrations (creates SQLite tables for admin/auth — optional but harmless):

```bash
docker compose exec api python manage.py migrate
```

---

## 9. Smoke test

On the server:

```bash
cd /opt/kleio
./scripts/smoke-check.sh
```

Or from your laptop:

```bash
curl -fsS http://SERVER_IP:8000/api/health
# expect: {"status":"ok"}

open http://SERVER_IP:3000
```

Manual checks:

- [ ] Landing page loads  
- [ ] Sign-in with Clerk works  
- [ ] Create a Reddit/HN keyword  
- [ ] `docker compose logs worker --tail 100` shows monitoring activity  

---

## 10. Day-2 operations

```bash
cd /opt/kleio

# Update code
git pull
docker compose up --build -d

# Logs
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f ui

# Restart one service
docker compose restart worker

# Stop everything
docker compose down
```

**If you change `SERVER_IP` or public URLs**, update `.env` + `BE/.env`, then **rebuild UI** (URLs are baked at build time):

```bash
docker compose build --no-cache ui
docker compose up -d ui
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Can’t SSH | Check Hetzner firewall / security group for port 22 |
| UI loads, API CORS errors | `CORS_ALLOWED_ORIGINS` must be exactly `http://SERVER_IP:3000` |
| Clerk sign-in fails | Add IP URL in Clerk dashboard; rebuild UI if publishable key wrong |
| API 400 DisallowedHost | Add IP to `ALLOWED_HOSTS` |
| Worker restart loop | `docker compose logs worker` — often Mongo/env; or Chrome OOM → upgrade to 8GB |
| Atlas timeout | Whitelist `SERVER_IP` in Atlas Network Access |
| `docker compose` not found | Re-run `get.docker.com` install; log out/in |

---

## When you get a domain (later)

1. Point DNS A record → `SERVER_IP`  
2. Install Caddy/Nginx for HTTPS on 443  
3. Set `SECURE_SSL_REDIRECT=True`, `USE_X_FORWARDED_HOST=True`  
4. Rebuild UI with `https://your.domain`  
5. Update Clerk + CORS + `ALLOWED_HOSTS`  

See also: [DEPLOYMENT.md](./DEPLOYMENT.md) · **Auto-deploy (CD):** [DEPLOYMENT.cd.md](./DEPLOYMENT.cd.md) · **Worker watchdog:** [DEPLOYMENT.worker-watchdog.md](./DEPLOYMENT.worker-watchdog.md)

---

## Quick command cheat sheet

```bash
ssh root@SERVER_IP
cd /opt/kleio
docker compose up --build -d
docker compose ps
./scripts/smoke-check.sh
docker compose logs -f worker
```
