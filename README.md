# Kleio - Social Mention Monitoring Platform

A comprehensive social listening tool that monitors keywords across Reddit and Hacker News, with email notifications via SendGrid.

## Features

- **Multi-platform monitoring**: Reddit and Hacker News
- **Real-time keyword tracking**: OAuth-based Reddit API integration
- **Email notifications**: SendGrid integration for instant alerts
- **User authentication**: Clerk integration with toggle for testing
- **Modern UI**: Next.js with shadcn/ui components
- **Scalable backend**: Spring Boot with MongoDB

## Architecture

- **Frontend**: Next.js 14 with TypeScript, Clerk auth, shadcn/ui
- **Backend**: Spring Boot 3.5 with Java 17
- **Database**: MongoDB
- **Email**: SendGrid
- **Authentication**: Clerk (toggleable for testing)

## Quick Start

### Prerequisites

- Java 17+
- Node.js 18+
- MongoDB
- Reddit API credentials
- SendGrid API key
- Clerk account (optional)

### Backend Setup

1. **Clone and navigate to backend**:

   ```bash
   cd BE
   ```

2. **Set up Reddit API credentials**:

   - Go to https://www.reddit.com/prefs/apps
   - Create a new app (select "script")
   - Note your Client ID and Client Secret
   - Set environment variables:

   ```bash
   export REDDIT_CLIENT_ID=your_client_id_here
   export REDDIT_CLIENT_SECRET=your_client_secret_here
   ```

3. **Set up SendGrid**:

   ```bash
   export SENDGRID_API_KEY=your_sendgrid_api_key
   ```

4. **Start MongoDB**:

   ```bash
   # Start MongoDB service
   mongod
   ```

5. **Run the backend**:
   ```bash
   ./mvnw spring-boot:run
   ```

### Frontend Setup

1. **Navigate to frontend**:

   ```bash
   cd UI
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure authentication** (optional):

   - Set up Clerk account
   - Add environment variables:

   ```bash
   export NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
   export CLERK_SECRET_KEY=your_clerk_secret
   ```

   - Or disable auth for testing:

   ```bash
   export NEXT_PUBLIC_AUTH_ENABLED=false
   ```

4. **Run the frontend**:
   ```bash
   npm run dev
   ```

## Reddit API Integration

The platform uses Reddit's OAuth 2.0 API for real-time keyword monitoring:

### How it works:

1. **OAuth Authentication**: Uses client credentials flow for app-level access
2. **Token Management**: Automatically refreshes access tokens
3. **Search API**: Queries Reddit's search endpoint with keywords
4. **Rate Limiting**: Respects Reddit's API limits (60 requests/minute)
5. **Data Parsing**: Extracts post details (title, author, score, etc.)

### API Endpoints:

- `GET /api/keywords` - List user's keywords
- `POST /api/keywords` - Add new keyword
- `PUT /api/keywords/{id}/toggle` - Enable/disable keyword
- `DELETE /api/keywords/{id}` - Delete keyword
- `GET /api/reddit/search?keyword={keyword}` - Test Reddit search

### Example Reddit Search Response:

```json
{
  "id": "abc123",
  "title": "Post title containing keyword",
  "author": "username",
  "subreddit": "programming",
  "url": "https://reddit.com/r/programming/comments/...",
  "score": 42,
  "createdUtc": 1640995200
}
```

## Hacker News Integration

Uses Hacker News' public Firebase API:

- **Top Stories**: Monitors top 30 stories
- **Keyword Matching**: Searches titles for keywords
- **Real-time**: Checks for new mentions
- **No Authentication**: Public API, no rate limits

## Email Notifications

SendGrid integration for instant alerts:

- **Template-based**: Professional email templates
- **Real-time**: Immediate notification on mention
- **Rich content**: Includes mention details and links
- **Configurable**: Easy to customize templates

## Authentication

Clerk integration with toggle for testing:

### With Authentication (Production):

- User registration/login
- JWT-based API security
- User-specific data isolation
- Route protection

### Without Authentication (Testing):

- Set `NEXT_PUBLIC_AUTH_ENABLED=false`
- Skip login for development
- All features accessible
- Faster testing workflow

## Development

### Backend Structure:

```
BE/src/main/java/com/kleio/tracker/
├── controller/     # REST API endpoints
├── service/        # Business logic (Reddit, HN, Email)
├── model/          # Data models
├── repository/     # MongoDB repositories
├── config/         # Configuration
└── KleioApplication.java
```

### Frontend Structure:

```
UI/src/
├── app/           # Next.js app router
├── components/    # Reusable UI components
├── lib/           # Utilities and API client
└── middleware.ts  # Clerk middleware
```

### Key Services:

1. **RedditApiService**: OAuth integration, search, token management
2. **HackerNewsScrapingService**: HN API integration, story processing
3. **EmailService**: SendGrid integration, notification templates
4. **KeywordService**: CRUD operations, user management

## Environment Variables

### Backend (.env or system):

```bash
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
SENDGRID_API_KEY=your_sendgrid_key
MONGODB_URI=mongodb://localhost:27017/kleio
```

### Frontend (.env.local):

```bash
NEXT_PUBLIC_AUTH_ENABLED=true
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## API Documentation

### Keywords API:

- `GET /api/keywords` - Get user's keywords
- `POST /api/keywords` - Create keyword
- `PUT /api/keywords/{id}` - Update keyword
- `DELETE /api/keywords/{id}` - Delete keyword
- `PUT /api/keywords/{id}/toggle` - Toggle keyword status

### Mentions API:

- `GET /api/mentions` - Get user's mentions
- `POST /api/mentions` - Create mention (internal)

### Platform APIs:

- `GET /api/reddit/search?keyword={keyword}` - Test Reddit search
- `GET /api/hackernews/search?keyword={keyword}` - Test HN search

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see LICENSE file for details.
