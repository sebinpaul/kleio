# Continuous Deploy (CD) — blind follow guide

**Goal:** After this, you only `git push origin main` from your laptop. GitHub SSHs into the VPS and runs `git pull` + `docker compose up --build -d`.

**Already in the repo (after you pull/push these files):**
- `.github/workflows/ci.yml` — tests first, then SSH deploy to the VPS (only if tests pass on `main`)
- `scripts/deploy.sh` — commands run on the VPS

Do the stages **in order**. Do not skip.

---

## Stage 0 — Prerequisites (2 min)

You need:

- [ ] Laptop with git + SSH
- [ ] Access to GitHub repo `sebinpaul/kleio` (or your fork)
- [ ] VPS still reachable:

```bash
ssh -i ~/.ssh/personal_work -o IdentitiesOnly=yes root@77.42.71.149
```

- [ ] On the VPS, `/opt/kleio` exists and `docker compose ps` works
- [ ] On the VPS, `git pull` already works (public repo, or deploy key / PAT already set up)

**If `git pull` on the VPS asks for a password or fails**, fix that first (see Appendix A) before CD.

---

## Stage 1 — Create a dedicated deploy SSH key (on your laptop)

This key is **only** for GitHub Actions → VPS. Do **not** reuse `personal_work` if you can avoid it (easier to revoke later).

On your **laptop**:

```bash
ssh-keygen -t ed25519 -C "github-actions-kleio-deploy" -f ~/.ssh/kleio_deploy -N ""
```

That creates:

- `~/.ssh/kleio_deploy` — **private** (goes to GitHub Secrets — never commit)
- `~/.ssh/kleio_deploy.pub` — **public** (goes on the VPS)

Show the public key (you will paste it on the VPS next):

```bash
cat ~/.ssh/kleio_deploy.pub
```

Leave this terminal open or copy the line that starts with `ssh-ed25519`.

---

## Stage 2 — Install the public key on the VPS

SSH in with your normal key:

```bash
ssh -i ~/.ssh/personal_work -o IdentitiesOnly=yes root@77.42.71.149
```

On the **VPS**, run (paste your **public** key in place of `PASTE_PUBLIC_KEY_HERE`):

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

Example (one line, your key will differ):

```bash
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... github-actions-kleio-deploy' >> ~/.ssh/authorized_keys
```

Still on the VPS, confirm the app directory:

```bash
cd /opt/kleio
git remote -v
git status
docker compose ps
```

Exit:

```bash
exit
```

### Quick test from your laptop

GitHub will do the same kind of SSH. Test the new key:

```bash
ssh -i ~/.ssh/kleio_deploy -o IdentitiesOnly=yes root@77.42.71.149 'echo OK && hostname'
```

You must see `OK` and the hostname. If it asks for a password or fails, fix Stage 2 before continuing.

---

## Stage 3 — Add GitHub Secrets

1. Open the repo on GitHub in a browser.
2. Go to **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** for each of these:

| Name | Value |
|------|--------|
| `VPS_HOST` | `77.42.71.149` |
| `VPS_USER` | `root` |
| `VPS_SSH_KEY` | **Full contents** of `~/.ssh/kleio_deploy` (the **private** key) |

To copy the private key on your laptop:

```bash
cat ~/.ssh/kleio_deploy
```

Paste **everything**, including:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

4. Confirm secrets list shows `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`.

(SSH port is fixed to **22** in the workflow. If you change the server SSH port later, edit `port:` in `.github/workflows/ci.yml`.)

**Hetzner firewall:** port **22** must allow inbound SSH (you already opened this). GitHub Actions connects from the internet, so do not lock port 22 to only your home IP unless you also allow GitHub’s ranges (advanced — skip for now).

---

## Stage 4 — Put the workflow on `main`

On your **laptop**, in the kleio repo:

```bash
cd /Users/sjoseph/personal/kleio   # or your clone path
git status
git checkout main
git pull origin main
```

If `DEPLOYMENT.cd.md`, `.github/workflows/ci.yml`, and `scripts/deploy.sh` are not committed yet, commit and push them (or pull if they were pushed from another machine).

Then push to `main`:

```bash
git push origin main
```

That push should **trigger** the first deploy.

---

## Stage 5 — Watch the first deploy

1. Open GitHub → **Actions** tab.
2. Click the workflow run named **CI**.
3. Confirm **test** is green, then **deploy** runs and goes green.

**Success:** both jobs green; deploy log shows pull, compose build, smoke check passed.

**Failure:** if **test** is red, **deploy does not run**. If **deploy** is red, open that job’s log — see Stage 7.

First build can take **10–30 minutes** (especially the worker/Chrome image). Do not cancel early.

---

## Stage 6 — Confirm it worked

From your laptop:

```bash
curl -sS http://77.42.71.149:8000/api/health
curl -sS -o /dev/null -w "%{http_code}\n" http://77.42.71.149:3000
```

Expect: `{"status":"ok"}` and a `200` (or `307`/`302`).

On the VPS (optional):

```bash
ssh -i ~/.ssh/personal_work -o IdentitiesOnly=yes root@77.42.71.149
cd /opt/kleio
git log -1 --oneline
docker compose ps
```

`git log -1` should match the commit you just pushed.

---

## Stage 7 — Day-2: how you deploy forever

From your laptop, after any change:

```bash
git add -A
git commit -m "your message"
git push origin main
```

Then open **Actions** → **CI** and wait for **test** then **deploy** to go green.

You can also trigger a deploy without a new commit:

1. GitHub → **Actions** → **CI**
2. **Run workflow** → branch `main` → **Run workflow**
   (runs tests first; deploys only if tests pass)

Manual deploy (if Actions is down):

```bash
ssh -i ~/.ssh/personal_work -o IdentitiesOnly=yes root@77.42.71.149
cd /opt/kleio
./scripts/deploy.sh
```

---

## Stage 8 — Troubleshooting

| Symptom | Fix |
|---------|-----|
| Actions: `Permission denied (publickey)` | Public key not in VPS `authorized_keys`, or wrong private key in `VPS_SSH_KEY`. Re-do Stages 1–3. Re-test with `ssh -i ~/.ssh/kleio_deploy ...` |
| Actions: connection timeout | Hetzner firewall missing TCP **22**, or server off |
| Actions: `git pull` auth failed | VPS cannot talk to GitHub — Appendix A |
| Actions: `docker compose` fails | Read the log; often disk full or bad Dockerfile. SSH in and run `./scripts/deploy.sh` to reproduce |
| Smoke check fails | API/UI not up yet; check `docker compose ps` and `docker compose logs` |
| Deploy succeeded but UI looks old | Hard refresh browser; confirm `git log -1` on server |
| Env / Clerk keys missing after deploy | Normal — `.env` files are **not** in git. They stay on the server. Never commit them |

---

## What CD does **not** do

- Does **not** copy `.env` / `BE/.env` from your laptop (good — secrets stay on the VPS)
- Does **not** change Hetzner firewall or Clerk settings
- Does **not** deploy feature branches — only **`main`** (and manual “Run workflow”)

If you change `NEXT_PUBLIC_*` in the **server** root `.env`, you still need a rebuild (CD’s `docker compose up --build -d` already rebuilds when you push code; if you only edit `.env` on the server, run `./scripts/deploy.sh` or **Run workflow**).

---

## Appendix A — VPS cannot `git pull` (private repo)

On the VPS:

```bash
cd /opt/kleio
git pull origin main
```

If that fails with auth errors:

**Option 1 — Deploy key (read-only) for GitHub → clone**

1. On VPS: `ssh-keygen -t ed25519 -C "kleio-vps-git" -f ~/.ssh/kleio_github -N ""`
2. `cat ~/.ssh/kleio_github.pub` → add as **Deploy key** (read-only) in GitHub → repo → Settings → Deploy keys
3. Configure SSH for github.com on the VPS (`~/.ssh/config`):

```text
Host github.com
  IdentityFile ~/.ssh/kleio_github
  IdentitiesOnly yes
```

4. Ensure remote is SSH:

```bash
cd /opt/kleio
git remote set-url origin git@github.com:sebinpaul/kleio.git
git pull origin main
```

**Option 2 — HTTPS + fine-scoped PAT** (stored in git credential on VPS). Prefer deploy key when possible.

---

## Checklist (print / tick)

- [ ] Stage 1: `kleio_deploy` key created on laptop  
- [ ] Stage 2: public key on VPS; `ssh -i ~/.ssh/kleio_deploy ...` prints OK  
- [ ] Stage 3: GitHub secrets `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`  
- [ ] Stage 4: `ci.yml` on `main` pushed  
- [ ] Stage 5: Actions **CI** job green (test → deploy)  
- [ ] Stage 6: health URL still `ok`  

You’re done. CD is live.
