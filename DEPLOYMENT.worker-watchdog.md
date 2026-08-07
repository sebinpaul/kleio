# Worker watchdog (cron + Healthchecks email alerts)

When Mongo/DNS blips, the worker container can stay **Up** but stop monitoring.
The watchdog runs every 5 minutes: checks the worker, **restarts** it if needed, and
pings [Healthchecks.io](https://healthchecks.io) so you get email if it stays broken.

Also: the worker process **exits** after repeated Mongo/DNS errors so Docker’s
`restart: unless-stopped` can bring it back without waiting for cron.

---

## What deploy already does

`scripts/deploy.sh` (and GitHub CD) now:

- `chmod +x` on scripts  
- installs the **cron** line automatically if missing  

You do **not** need `crontab -e` after a normal deploy, unless cron was never installed and an old deploy ran before this change — then either redeploy or run the one-time cron install below.

You **do** still set `HEALTHCHECKS_PING_URL` once on the server (secrets stay out of git).

---

## One-time: Healthchecks email (required)

### A. Create the check in the browser

1. Open https://healthchecks.io and sign up / log in  
2. **Add Check**  
   - Name: `Kleio worker`  
   - Period: **5 minutes**  
   - Grace time: **5 minutes**  
3. Open the check → copy the **Ping URL**  
   Looks like: `https://hc-ping.com/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`  
4. Under **Integrations** / email, confirm your email is enabled for alerts  

### B. Put the URL on the VPS

SSH in, then:

```bash
ssh -i ~/.ssh/personal_work -o IdentitiesOnly=yes root@77.42.71.149
cd /opt/kleio
nano .env
```

Add this line (use **your** ping URL):

```env
HEALTHCHECKS_PING_URL=https://hc-ping.com/YOUR-UUID-HERE
```

Save (`Ctrl+O`, Enter, `Ctrl+X`).

Do **not** commit this file. It stays only on the server.

### C. Test

```bash
cd /opt/kleio
chmod +x scripts/worker-watchdog.sh
./scripts/worker-watchdog.sh
```

Expect `Worker healthy`. In Healthchecks, the check should go **up**.

---

## Cron (usually automatic via deploy)

**What is cron?**  
The server’s scheduler. `crontab -e` opens an editor to add scheduled jobs.  
We use it so the watchdog runs every 5 minutes without you SSHing in.

**After this deploy script change**, CD/deploy installs:

```cron
*/5 * * * * /opt/kleio/scripts/worker-watchdog.sh >> /var/log/kleio-worker-watchdog.log 2>&1
```

Verify:

```bash
crontab -l
```

If the line is missing (old server state), either run `./scripts/deploy.sh` once, or:

```bash
(crontab -l 2>/dev/null || true; echo '*/5 * * * * /opt/kleio/scripts/worker-watchdog.sh >> /var/log/kleio-worker-watchdog.log 2>&1') | crontab -
```

Watchdog log:

```bash
tail -f /var/log/kleio-worker-watchdog.log
```

---

## Live worker logs

```bash
cd /opt/kleio
docker compose logs -f worker
```

Last N lines only:

```bash
docker compose logs worker --tail 100 -f
```

`Ctrl+C` stops following (does not stop the worker).

---

## Quick checklist

- [ ] `HEALTHCHECKS_PING_URL` in `/opt/kleio/.env`  
- [ ] `./scripts/worker-watchdog.sh` prints healthy  
- [ ] Healthchecks dashboard shows **up**  
- [ ] `crontab -l` shows `worker-watchdog.sh`  
- [ ] `docker compose logs -f worker` shows monitoring activity  
