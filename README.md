# Kleio - Social Mention Monitoring Platform

A comprehensive social listening tool that monitors keywords across Reddit and Hacker News, with email notifications for instant alerts. Similar to F5Bot, Kleio allows users to track specific keywords and receive email notifications when mentions are detected.

## 🎯 Overview

Kleio is a mention monitoring tool that allows users to track specific keywords across online platforms like Reddit, Hacker News, Twitter, and LinkedIn. Whenever a keyword is detected, users receive email alerts with context and source links.

## ✨ Features

- **Multi-platform monitoring**: Reddit and Hacker News (Twitter and LinkedIn planned)
- **Real-time keyword tracking**: Automated scraping and monitoring
- **Email notifications**: Instant alerts with mention details and links
- **User authentication**: Secure login via Clerk
- **Modern UI**: Next.js with shadcn/ui components
- **Scalable backend**: Django with REST API
- **Keyword management**: Add, view, and delete keywords from dashboard
- **Duplicate prevention**: Smart deduplication to avoid spam

## 🏗️ Architecture

- **Frontend**: Next.js 14 with TypeScript, Clerk auth, shadcn/ui
- **Backend**: Django with Django Rest Framework (DRF)
- **Database**: MongoDB (flexible schema for mentions and keywords)
- **Email**: SendGrid/Resend/Mailgun integration
- **Authentication**: Clerk (JWT-based user verification)
- **Background Tasks**: Django Q or Celery for scheduled scraping

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB
- Reddit API credentials (optional for testing)
- SendGrid API key
- Clerk account

### Backend Setup

1. **Clone and navigate to backend**:

   ```bash
   cd BE
   ```

2. **Set up Python environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:

   ```bash
   export REDDIT_CLIENT_ID=your_client_id_here
   export REDDIT_CLIENT_SECRET=your_client_secret_here
   export SENDGRID_API_KEY=your_sendgrid_api_key
   export MONGODB_URI=mongodb://localhost:27017/kleio
   export CLERK_SECRET_KEY=your_clerk_secret_key
   ```

4. **Run Django migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Start the backend**:
   ```bash
   python manage.py runserver
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

3. **Configure environment variables**:

   ```bash
   export NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
   export CLERK_SECRET_KEY=your_clerk_secret
   export NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the frontend**:
   ```bash
   npm run dev
   ```

## 🔍 Platform Integrations

### Reddit Integration

- **OAuth Authentication**: Uses client credentials flow for app-level access
- **Search API**: Queries Reddit's search endpoint with keywords
- **Rate Limiting**: Respects Reddit's API limits
- **Data Parsing**: Extracts post details (title, author, score, etc.)

### Hacker News Integration

- **Algolia API**: Uses Hacker News' public Algolia API
- **Latest Posts**: Monitors recent posts for keyword matches
- **No Authentication**: Public API, no rate limits
- **Real-time**: Checks for new mentions regularly

## 📧 Email Notifications

- **Template-based**: Professional email templates
- **Real-time**: Immediate notification on mention
- **Rich content**: Includes mention details and source links
- **Configurable**: Easy to customize templates
- **Batch processing**: Efficient email delivery

## 🔐 Authentication

Clerk integration for secure user management:

- **User registration/login**: OAuth and email/password support
- **JWT-based API security**: Secure frontend-backend communication
- **User-specific data isolation**: Each user sees only their keywords and mentions
- **Route protection**: Secure dashboard access

## 🏗️ System Flow

1. **Authentication**: Clerk manages user sign up, login, and session
2. **Keyword Management**: Users add/remove keywords via dashboard
3. **Background Monitoring**: Django tasks poll platforms every X minutes
4. **Keyword Matching**: Each post/comment is checked against user keywords
5. **Notification**: Matched mentions trigger email alerts with context

## 📁 Project Structure

### Backend (Django):

```
BE/
├── kleio_backend/          # Django project settings
├── tracker/               # Main app
│   ├── models.py         # User, Keyword, Mention models
│   ├── views.py          # REST API endpoints
│   ├── serializers.py    # DRF serializers
│   ├── services/         # Business logic
│   │   ├── reddit_service.py
│   │   ├── hackernews_service.py
│   │   └── email_service.py
│   └── management/       # Custom Django commands
└── manage.py
```

### Frontend (Next.js):

```
UI/src/
├── app/                  # Next.js app router
│   ├── dashboard/        # Main dashboard pages
│   └── layout.tsx        # Root layout
├── components/           # Reusable UI components
│   ├── AddKeywordModal.tsx
│   ├── KeywordList.tsx
│   └── ui/              # shadcn/ui components
├── lib/                 # Utilities and API client
└── middleware.ts        # Clerk middleware
```

## 🔧 API Endpoints

### Keywords API:

- `GET /api/keywords/` - Get user's keywords
- `POST /api/keywords/` - Create new keyword
- `PUT /api/keywords/{id}/` - Update keyword
- `DELETE /api/keywords/{id}/` - Delete keyword
- `PUT /api/keywords/{id}/toggle/` - Toggle keyword status

### Mentions API:

- `GET /api/mentions/` - Get user's mentions
- `POST /api/mentions/` - Create mention (internal)

### Platform APIs:

- `GET /api/reddit/search/?keyword={keyword}` - Test Reddit search
- `GET /api/hackernews/search/?keyword={keyword}` - Test HN search

## 🛡️ Security & Performance

- **Clerk handles authentication security**
- **Input validation and sanitization**
- **Duplicate notification prevention**
- **Rate limiting for scrapers**
- **Secure email transport**
- **JWT-based API security**

## 🎯 MVP Features

- ✅ User sign up and login via Clerk
- ✅ Add, view, and delete keywords from dashboard
- ✅ Email notifications for keyword mentions
- ✅ Duplicate email prevention
- ✅ View current keyword list
- ✅ Regular polling of Reddit and HN
- ✅ Basic error handling

## 🚀 Future Enhancements

- **Additional platforms**: Twitter (X), LinkedIn, YouTube
- **Slack/webhook integrations**
- **Daily/weekly summary digests**
- **Custom alert frequency**
- **Team-based keyword tracking**
- **Admin dashboard**

## 🔧 Environment Variables

### Backend:

```bash
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
SENDGRID_API_KEY=your_sendgrid_key
MONGODB_URI=mongodb://localhost:27017/kleio
CLERK_SECRET_KEY=your_clerk_secret_key
```

### Frontend:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@kleio.com or join our Slack channel.
