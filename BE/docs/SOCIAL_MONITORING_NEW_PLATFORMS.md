# LinkedIn, Facebook, Quora Monitoring

Constraints: No user login, no outsourcing; prefer public scraping; use official APIs where feasible.

## Facebook
- Primary: Graph API for public Pages. Requires App Access Token (`KLEIO_FACEBOOK_APP_TOKEN`) or set per user in Settings (Facebook section).
- Inputs: Page IDs/usernames/URLs via Settings → Facebook. Also supports `page:<slug>`.
- Fields: message, permalink_url, created_time, from.
- Fallback: Public scraping of mbasic/m.facebook.com Page posts if token missing/unavailable.

## LinkedIn
- Public-only best effort via source URLs (hashtags/companies/profiles) configured in Settings.
- Many pages are login-gated; service detects gate and backs off for 6–12h.
- Extraction: og:title/og:description; no login, no comments.

## Quora
- Public search for each keyword; optional Topic URLs via Settings.
- Extraction: og:title/description from question/answer pages.

## Configuration
- Proxies: Manage in Settings → Proxies. All services use ProxyManager.
- Sources: Settings → LinkedIn / Facebook / Quora. One source per line. Facebook optional App Token stored per user.
- Intervals: Internal defaults 5–10 min; adjust in service if needed.

## Limitations
- LinkedIn coverage is limited by login-gates; articles/newsletters are most reliable.
- Facebook Graph API requires app review/permissions to read public Page content; rate limits apply.
- Quora may throttle; expect occasional backoffs.

## Integration
- Auto-monitor starts/stops platform services based on active Keywords.
- Services prefer Settings sources; otherwise fall back to per-keyword platformSpecificFilters.

## Data
- Mentions stored with platform, source_url, title/body, author (if available), timestamps.
- Deduplication by source_url and keyword.

