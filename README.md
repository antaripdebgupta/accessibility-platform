# Accessibility Evaluation Platform Prototype

End-to-end accessibility evaluation platform implementing WCAG-EM methodology.

## Tech Stack

### Backend

- **FastAPI** — Async Python web framework
- **PostgreSQL** — Primary database
- **Redis** — Task queue broker & caching
- **Celery** — Distributed task queue
- **Playwright** — Browser automation for accessibility scanning
- **Firebase Admin** — Authentication

### Frontend

- **Vue 3** — Composition API
- **Pinia** — State management
- **Vue Router** — Client-side routing
- **Tailwind CSS** — Utility-first styling
- **Axios** — HTTP client

### Infrastructure

- **Docker Compose** — Container orchestration
- **Nginx** — Reverse proxy
- **MinIO** — S3-compatible object storage

## Getting Started

### Prerequisites

- Docker Desktop
- Node.js 20+
- Python 3.12+
- Git

### Environment Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd accessibility-platform
   ```

2. Copy environment file:

   ```bash
   cp .env.example .env
   ```

3. (Optional) Configure Firebase:
   - Create a Firebase project at console.firebase.google.com
   - Enable Email/Password authentication
   - Download service account key as `firebase_sa.json`
   - Place it in the project root (it's gitignored)
   - Update `.env` with your Firebase project ID

4. Start the stack:

   ```bash
   make up
   ```

5. Verify everything is running:

   ```bash
   # Check API health
   curl http://localhost/api/v1/health

   # Open frontend
   open http://localhost
   ```

## Development

### Using Docker Compose (recommended)

```bash
# Start all services
make up

# View logs
make logs

# Stop services
make down

# Reset database
make reset-db
```

### Development Mode (with hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Running Backend Locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start API server
uvicorn main:app --reload --port 8000
```

### Running Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

## API Documentation

- **Swagger UI**: http://localhost/api/v1/docs
- **ReDoc**: http://localhost/api/v1/redoc

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   Browser   │────▶│    Nginx    │────▶│   Vue SPA    │
│             │     │  (Reverse   │     │  (Frontend)  │
└─────────────┘     │   Proxy)    │     └──────────────┘
                    │             │
                    │             │     ┌──────────────┐
                    │             │────▶│   FastAPI    │
                    └─────────────┘     │   (Backend)  │
                                        └──────┬───────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
            ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
            │  PostgreSQL  │           │    Redis     │           │    MinIO     │
            │  (Database)  │           │   (Broker)   │           │  (Storage)   │
            └──────────────┘           └──────┬───────┘           └──────────────┘
                                              │
                                              ▼
                                      ┌──────────────┐
                                      │   Celery     │
                                      │   Worker     │
                                      │ (Playwright) │
                                      └──────────────┘
```

## What's Implemented

| Feature                    | Status   | Description                                      |
| -------------------------- | -------- | ------------------------------------------------ |
| **Authentication**         | Complete | Firebase Auth with dev bypass token              |
| **Evaluation CRUD**        | Complete | Create, read, update, soft-delete evaluations    |
| **Page Discovery**         | Complete | Playwright-based crawler with robots.txt support |
| **Accessibility Scanning** | Complete | axe-core integration with parallel scanning      |
| **Findings Management**    | Complete | Per-criterion verdict review (pass/fail/N/A)     |
| **WCAG Criteria**          | Complete | All 50 WCAG 2.1 Level A & AA criteria seeded     |
| **PDF Reports**            | Complete | WeasyPrint-generated WCAG-EM conformance reports |
| **CSV/EARL Export**        | Complete | Machine-readable accessibility findings export   |
| **Audit Logging**          | Complete | Full audit trail for compliance                  |
| **Multi-org Support**      | Complete | Organisation-scoped evaluations                  |
| **Responsive UI**          | Complete | Mobile-friendly Vue 3 + Tailwind interface       |

## WCAG-EM Workflow

The platform implements the [WCAG-EM methodology](https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/):

1. **Define Scope** — Set target URL and evaluation parameters
2. **Explore Website** — Crawl and discover pages automatically
3. **Select Sample** — Choose representative pages for testing
4. **Audit Sample** — Run axe-core accessibility tests
5. **Report Findings** — Review verdicts and generate conformance report

## Documentation

- [Developer Setup Guide](./DEVELOPER_SETUP.md) — Complete local setup instructions
- [Firebase Setup](./FIREBASE_SETUP.md) — Authentication configuration
- [API Documentation](http://localhost/api/v1/docs) — Interactive Swagger UI
