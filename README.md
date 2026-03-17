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
│   ├── core/                     # Main Django app
│   │   ├── models.py             # Keyword, Mention models (MongoEngine)
│   │   ├── views.py              # REST API endpoints
│   │   ├── serializers.py
│   │   ├── enums.py              # Platform, MatchMode, ContentType enums
│   │   ├── services/
│   │   │   ├── auto_monitor_service.py
│   │   │   ├── matching_engine.py
│   │   │   ├── email_service.py
│   │   │   ├── clerk_service.py
│   │   │   ├── instant_notification_service.py
│   │   │   └── proxy_service.py
│   │   └── management/commands/
│   │       └── auto_monitor.py   # Background monitoring command
│   └── platforms/                # Platform integrations
│       ├── reddit/services/      # PRAW + realtime stream
│       ├── hackernews/services/  # Algolia API
│       ├── twitter/services/     # Scraping-based
│       ├── youtube/services/     # Invidious API
│       ├── linkedin/services/    # Scraping-based
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
# MongoDB
MONGODB_URI=mongodb://localhost:27017/kleio
MONGODB_DATABASE=kleio

# Reddit API (https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=KleioMentionTracker/1.0

# Email (https://resend.com)
RESEND_API_KEY=
RESEND_FROM_EMAIL=alerts@yourdomain.com

# Clerk (https://clerk.com) — used for user email lookup
CLERK_SECRET_KEY=
```

Start the server:

```bash
python manage.py migrate
python manage.py runserver
```

Start background monitoring (separate terminal):

```bash
python manage.py auto_monitor
```

### Frontend

```bash
cd UI
npm install
```

Create `UI/.env`:

```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_ENABLED=true
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Start the dev server:

```bash
npm run dev
```

The app runs at `http://localhost:3000`. The backend API runs at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/keywords/` | List user's keywords (filtered by `?platform=`) |
| POST | `/api/keywords/` | Create keyword |
| PUT | `/api/keywords/{id}/` | Update keyword |
| DELETE | `/api/keywords/{id}/` | Delete keyword |
| PUT | `/api/keywords/{id}/toggle/` | Toggle keyword on/off |
| GET | `/api/mentions/` | List user's mentions |
| GET | `/api/reddit/search/?keyword=` | Test Reddit search |
| GET | `/api/hackernews/search/?keyword=` | Test Hacker News search |

All endpoints require a Clerk JWT in the `Authorization` header. The frontend handles this automatically.

## Platforms

| Platform | Method | Status |
|----------|--------|--------|
| Reddit | PRAW API + realtime SubredditStream | Active |
| Hacker News | Algolia public API | Active |
| Twitter | Web scraping | Active |
| YouTube | Invidious API | Active |
| LinkedIn | Web scraping | Active |
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
