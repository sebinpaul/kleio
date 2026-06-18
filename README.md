# Kleio

Social mention monitoring platform. Track keywords across Reddit, Hacker News, Twitter, YouTube, LinkedIn, Facebook, and Quora. Get email alerts when mentions are detected.

## Architecture

```
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│  Frontend (UI/)                 │      │  Backend (BE/)                  │
│  Next.js 15 · App Router       │─────▶│  Django 5 · DRF                 │
│  Tailwind · shadcn/ui          │ REST │  MongoEngine                    │
│  Clerk (auth)                   │      │  Clerk (JWT verification)       │
└─────────────────────────────────┘      └──────────┬──────────────────────┘
                                                    │
                                         ┌──────────▼──────────┐
                                         │  MongoDB             │
                                         │  Keywords · Mentions │
                                         └──────────┬──────────┘
                                                    │
                                         ┌──────────▼──────────┐
                                         │  Platform Services   │
                                         │  Reddit (PRAW)       │
                                         │  Hacker News (Algolia)│
                                         │  Twitter · YouTube   │
                                         │  LinkedIn · Facebook │
                                         │  Quora               │
                                         └──────────┬──────────┘
                                                    │
                                         ┌──────────▼──────────┐
                                         │  Resend (email)      │
                                         └─────────────────────┘
```

**Frontend:** Next.js 15 with TypeScript, Tailwind CSS, shadcn/ui components, Clerk authentication, Framer Motion (minimal — expand/collapse only).

**Backend:** Django 5 with Django REST Framework. MongoDB via MongoEngine for keywords and mentions. Platform-specific scraping services. Resend for email notifications. Clerk JWT for API auth.

**Database:** MongoDB (keywords, mentions, platform data). SQLite fallback for Django internals.

## Project Structure

```
kleio/
├── BE/                           # Django backend
│   ├── manage.py
│   ├── settings.py
│   ├── urls.py
│   ├── requirements.txt
│   ├── DEPLOYMENT.example.md   # Deployment checklist template (copy to DEPLOYMENT.local.md)
│   ├── core/                     # Main Django app
│   │   ├── models.py             # Keyword, Mention models (MongoEngine)
│   │   ├── views.py              # REST API endpoints
│   │   ├── authentication.py     # Clerk JWT authentication
│   │   ├── serializers.py
│   │   ├── enums.py              # Platform, MatchMode, ContentType enums
│   │   ├── services/
│   │   │   ├── auto_monitor_service.py
│   │   │   ├── matching_engine.py
│   │   │   ├── email_service.py
│   │   │   ├── clerk_service.py
│   │   │   └── instant_notification_service.py
│   │   └── management/commands/
│   │       └── auto_monitor.py   # Background monitoring command
│   └── platforms/                # Platform integrations
│       ├── reddit/services/      # PRAW + realtime stream
│       ├── hackernews/services/  # Algolia API
│       ├── twitter/services/     # Scraping-based
│       ├── youtube/services/     # Invidious API
│       ├── linkedin/services/    # Voyager API (linkedin-api)
│       ├── facebook/services/    # Public page scraping
│       └── quora/services/       # Scraping-based
│
└── UI/                           # Next.js frontend
    └── src/
        ├── app/
        │   ├── page.tsx          # Landing page (server component + SEO metadata)
        │   ├── _landing.tsx      # Landing page UI (client component)
        │   ├── dashboard/
        │   │   ├── layout.tsx    # Auth guard + sidebar layout
        │   │   ├── page.tsx      # Overview — all platforms + all keywords
        │   │   ├── reddit/       # Platform-specific keyword management
        │   │   ├── hackernews/
        │   │   ├── twitter/
        │   │   ├── youtube/
        │   │   ├── linkedin/
        │   │   ├── facebook/
        │   │   └── quora/
        │   ├── sign-in/          # Clerk sign-in
        │   └── sign-up/          # Clerk sign-up
        ├── components/
        │   ├── PlatformDashboard.tsx  # Shared dashboard layout for all platforms
        │   ├── KeywordList.tsx        # Keyword CRUD list (real API)
        │   ├── KeywordModal.tsx       # Add/edit keyword form
        │   ├── DeleteKeywordModal.tsx
        │   └── Sidebar.tsx
        └── lib/
            ├── api.ts            # Backend API client
            ├── enums.ts          # Platform, MatchMode, ContentType
            ├── platforms.tsx      # Platform configs (icons, colors)
            └── utils.ts
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB running locally (or a remote URI)
- Reddit API credentials (for Reddit monitoring)
- Resend API key (for email notifications)
- Clerk account (for authentication)

### Backend

```bash
cd BE
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `BE/.env`:

```env
# Django
DEBUG=True
DJANGO_SECRET_KEY=<generate-with-command-below>
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGODB_URI=mongodb://localhost:27017/kleio
MONGODB_DATABASE=kleio

# Clerk — API auth + email lookup
CLERK_SECRET_KEY=
# CLERK_JWT_KEY=                    # optional PEM public key (recommended for prod)
# CLERK_AUTHORIZED_PARTIES=http://localhost:3000
# CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Reddit API (https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=KleioMentionTracker/1.0

# Email (https://resend.com)
RESEND_API_KEY=
RESEND_FROM_EMAIL=alerts@yourdomain.com

# LinkedIn (use a dedicated account, not personal)
KLEIO_LI_USER=your-linkedin-email@example.com
KLEIO_LI_PASS=your-linkedin-password
# Or use li_at cookie instead of credentials (copy from browser dev tools):
# KLEIO_LINKEDIN_LI_AT=AQEDAx...
# Poll interval in seconds (default 300):
# KLEIO_LINKEDIN_CHECK_INTERVAL_SEC=300
```

Generate a Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Start the server:

```bash
python manage.py migrate
python manage.py runserver
```

Start background monitoring (separate terminal):

```bash
python manage.py auto_monitor start
```

### Frontend

```bash
cd UI
npm install
```

Create `UI/.env`:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Start the dev server:

```bash
npm run dev
```

The app runs at `http://localhost:3000`. The backend API runs at `http://localhost:8000`.

## Deployment

For production environment variables, Clerk/CORS alignment, and a pre-deploy checklist, copy and fill in:

```bash
cp BE/DEPLOYMENT.example.md BE/DEPLOYMENT.local.md
```

`DEPLOYMENT.local.md` is gitignored for your environment-specific URLs and notes.

## API Endpoints

All keyword endpoints require a Clerk JWT in the `Authorization` header. The frontend sends this automatically via `getToken()`.

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | No | Health check |
| GET | `/api/keywords` | Yes | List current user's keywords |
| POST | `/api/keywords` | Yes | Create keyword |
| PUT | `/api/keywords/{id}` | Yes | Update keyword |
| DELETE | `/api/keywords/{id}` | Yes | Delete keyword |
| PATCH | `/api/keywords/{id}/toggle` | Yes | Toggle keyword on/off |

Platform-scoped variants use `/api/platforms/{platform}/keywords` (same methods).

Mentions are created by background monitoring and emailed via Resend; there is no public mentions API yet.

## Platforms

| Platform | Method | Status |
|----------|--------|--------|
| Reddit | PRAW API + realtime SubredditStream | Active |
| Hacker News | Algolia public API | Active |
| Twitter | Web scraping | Active |
| YouTube | Invidious API | Active |
| LinkedIn | Voyager API (linkedin-api) | Active |
| Facebook | Public page scraping | Active |
| Quora | Web scraping | Active |

## Keyword Configuration

Each keyword supports:

- **Match mode:** Exact, Contains, Word Boundary, Starts With, Ends With
- **Case sensitivity:** Case insensitive (default), case sensitive
- **Content types:** Titles, Body, Comments
- **Platform filters:** Subreddits, hashtags, channels, pages, etc.
- **Notifications:** Email alerts via Resend

## System Flow

1. User signs up via Clerk and adds keywords through the dashboard
2. `auto_monitor` management command polls each platform on a schedule
3. New posts/comments are checked against user keywords via the matching engine
4. Matches are saved as mentions and trigger email notifications via Resend
5. Users view and manage keywords per-platform in the dashboard

## License

MIT
