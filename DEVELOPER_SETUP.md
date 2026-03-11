# Developer Setup Guide

Complete guide for setting up the WCAG Accessibility Evaluation Platform locally.

## Prerequisites

Before starting, ensure you have:

- **Docker Desktop** (v24+) - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Node.js 20+** (for Firebase emulator) - [Download](https://nodejs.org/)
- **curl** or **Postman** (for API testing)

Verify installations:

```bash
docker --version    # Docker version 24.x+
docker compose version  # Docker Compose version v2.x+
node --version      # v20.x+
git --version       # git version 2.x+
```

---

## Quick Start (After Cloning)

### Step 1: Clone the Repository

```bash
git clone https://github.com/antaripdebgupta/accessibility-platform.git
cd accessibility-platform
```

### Step 2: Create Environment File

```bash
cp .env.example .env
```

The default `.env` works out-of-box. Key variables:

```env
ENV=development
POSTGRES_USER=a11y
POSTGRES_PASSWORD=a11ypass
POSTGRES_DB=accessibility_db
DEV_BYPASS_TOKEN=dev-bypass-token-local-only
```

### Step 3: Install Firebase CLI (Optional)

Only needed if using Firebase emulator for auth:

```bash
npm install
npm install -g firebase-tools
```

### Step 4: Start All Services

```bash
make dev
```

This command:

1. Builds all Docker images
2. Starts PostgreSQL, Redis, MinIO, API, Worker, Frontend, Nginx
3. Runs database migrations automatically
4. Seeds WCAG criteria (50 guidelines) and dev user

**First run takes 3-5 minutes** (downloading images, building).

### Step 5: Verify Setup

Wait for all containers to be healthy, then:

```bash
# Check container status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Test health endpoint
curl http://localhost/api/v1/health
# Expected: {"status":"ok"}
```

### Step 6: Access the Application

| Service                | URL                           |
| ---------------------- | ----------------------------- |
| **Frontend**           | http://localhost              |
| **API Docs (Swagger)** | http://localhost/api/v1/docs  |
| **API Docs (ReDoc)**   | http://localhost/api/v1/redoc |
| **MinIO Console**      | http://localhost:9001         |

---

## Complete Setup Verification

Run this checklist to confirm everything works:

```bash
# 1. All containers running
docker ps | grep a11y_ | wc -l
# Expected: 7

# 2. Database tables created
docker compose exec postgres psql -U a11y -d accessibility_db -c "\dt" | grep -c "public"
# Expected: 9

# 3. WCAG criteria seeded
docker compose exec postgres psql -U a11y -d accessibility_db -c "SELECT COUNT(*) FROM wcag_criterion;"
# Expected: 50

# 4. Dev user seeded
docker compose exec postgres psql -U a11y -d accessibility_db -c "SELECT email FROM users;"
# Expected: dev@example.com

# 5. API responding
curl -s http://localhost/api/v1/health | jq .
# Expected: {"status":"ok"}
```

## Daily Development Commands

### Using Makefile (Recommended)

| Command          | Description                                    |
| ---------------- | ---------------------------------------------- |
| `make dev`       | Start all services in dev mode with hot reload |
| `make up`        | Start in production mode                       |
| `make down`      | Stop all services                              |
| `make logs`      | View all container logs                        |
| `make migrate`   | Run database migrations                        |
| `make seed`      | Seed WCAG criteria + dev user                  |
| `make reset-db`  | Reset database (destroys all data)             |
| `make shell-api` | Bash shell in API container                    |
| `make shell-db`  | PostgreSQL psql shell                          |

### Without Makefile

```bash
# Start dev mode---------------------------------------------------------------------------------------------------
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f          # All services
docker compose logs -f api      # API only
docker compose logs -f frontend # Frontend only

# Stop services
docker compose down
```

---

## API Testing Guide

### Authentication

For local development, use the **dev bypass token** (no Firebase required):

```
Authorization: Bearer dev-bypass-token-local-only
```

This creates/uses a dev user (`dev@example.com`) with owner role in "Dev Org".

> **Note**: Bypass only works when `ENV=development` in `.env`

### Get Your Org ID

First, call the auth endpoint to get your organisation ID:

```bash
curl -s -X POST http://localhost/api/v1/auth/me \
  -H "Authorization: Bearer dev-bypass-token-local-only" | jq .
```

Response:

```json
{
  "id": "...",
  "email": "dev@example.com",
  "organisations": [
    {
      "id": "2a2db11a-5f8f-444f-86ad-44dfd9d22087", // <- Use this as X-Org-Id
      "name": "Dev Org",
      "role": "OWNER"
    }
  ]
}
```

### Complete API Test Suite

Set your Org ID as a variable for convenience:

```bash
export ORG_ID="2a2db11a-5f8f-444f-86ad-44dfd9d22087"  # Replace with your actual ID
export AUTH="Authorization: Bearer dev-bypass-token-local-only"
```

#### 1. Health Check (No Auth Required)

```bash
curl -s http://localhost/api/v1/health | jq .
# Expected: {"status":"ok"}
```

#### 2. Auth - Get Current User

```bash
curl -s -X POST http://localhost/api/v1/auth/me \
  -H "$AUTH" | jq .
# Expected: User object with email and organisations
```

#### 3. Create Evaluation

```bash
curl -s -X POST http://localhost/api/v1/evaluations \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Website Audit",
    "target_url": "https://example.com",
    "description": "WCAG 2.1 AA compliance check"
  }' | jq .
# Expected: 201 Created with evaluation object
```

#### 4. List Evaluations

```bash
curl -s "http://localhost/api/v1/evaluations" \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" | jq .
# Expected: {"items": [...], "total": N, "page": 1, "page_size": 20}
```

#### 5. Get Single Evaluation

```bash
# Replace with actual evaluation ID from create response
EVAL_ID="your-evaluation-id-here"

curl -s "http://localhost/api/v1/evaluations/$EVAL_ID" \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" | jq .
# Expected: Full evaluation object
```

#### 6. Update Evaluation

```bash
curl -s -X PATCH "http://localhost/api/v1/evaluations/$EVAL_ID" \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title", "status": "IN_PROGRESS"}' | jq .
# Expected: 200 with updated evaluation
```

#### 7. Delete Evaluation (Soft Delete)

```bash
curl -s -X DELETE "http://localhost/api/v1/evaluations/$EVAL_ID" \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" \
  -w "HTTP Status: %{http_code}\n"
# Expected: HTTP Status: 204
```

### Error Response Testing

#### 401 Unauthorized (No Token)

```bash
curl -s http://localhost/api/v1/evaluations | jq .
# Expected: {"detail":"Not authenticated"}
```

#### 404 Not Found

```bash
curl -s "http://localhost/api/v1/evaluations/00000000-0000-0000-0000-000000000000" \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" | jq .
# Expected: {"detail":"Evaluation project with ID '...' not found"}
```

#### 422 Validation Error

```bash
curl -s -X POST http://localhost/api/v1/evaluations \
  -H "$AUTH" \
  -H "X-Org-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{"title": ""}' | jq .
# Expected: {"detail":[{"type":"value_error","loc":["body","title"],...}]}
```

---

## Access Points

### Application URLs

| Service    | URL                           | Description          |
| ---------- | ----------------------------- | -------------------- |
| Frontend   | http://localhost              | Vue 3 SPA            |
| API        | http://localhost/api/v1/      | FastAPI backend      |
| Swagger UI | http://localhost/api/v1/docs  | Interactive API docs |
| ReDoc      | http://localhost/api/v1/redoc | API documentation    |

### Infrastructure URLs

| Service       | URL                   | Credentials             |
| ------------- | --------------------- | ----------------------- |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| PostgreSQL    | localhost:5432        | a11y / a11ypass         |
| Redis         | localhost:6379        | (no auth)               |

### Firebase Emulator (Optional)

| Service            | URL                   |
| ------------------ | --------------------- |
| Emulator UI        | http://127.0.0.1:4000 |
| Auth Emulator      | http://127.0.0.1:9099 |
| Firestore Emulator | http://127.0.0.1:8080 |

Start emulator:

```bash
firebase emulators:start
```

---

## Development Features

- **Hot Reload**: Both frontend and backend auto-reload on code changes
- **Frontend**: Vite HMR (instant updates)
- **Backend**: Uvicorn with `--reload` flag
- **Database**: Alembic migrations with auto-upgrade on startup
- **Auth Bypass**: Dev token for local testing without Firebase

---

## axe-core Setup

The accessibility scanner uses [axe-core](https://github.com/dequelabs/axe-core) for WCAG testing. The `axe.min.js` file is included in the repository, but if you need to update it:

### Download Latest axe-core

```bash
# Download latest version
curl -L https://unpkg.com/axe-core/axe.min.js -o backend/scanners/axe.min.js

# Or specific version
curl -L https://unpkg.com/axe-core@4.10.0/axe.min.js -o backend/scanners/axe.min.js
```

### Verify Installation

```bash
# Check axe-core version
head -1 backend/scanners/axe.min.js
# Should show: /*! axe v4.x.x ...
```

The scanner injects this file into pages via Playwright during accessibility audits.

---

## MinIO Storage Console

MinIO provides S3-compatible object storage for PDF reports and exports.

### Access MinIO Console

| URL          | http://localhost:9001 |
| ------------ | --------------------- |
| **Username** | minioadmin            |
| **Password** | minioadmin            |

### Storage Buckets

The platform uses these buckets (created automatically):

- `reports` — Generated PDF conformance reports
- `exports` — CSV and EARL export files

### Presigned URLs

Download links for reports use presigned URLs that:

- Expire after 72 hours
- Are generated on-demand via the API
- Don't require authentication to download

### Manual Bucket Operations

```bash
# List buckets
docker compose exec minio mc ls local/

# List reports
docker compose exec minio mc ls local/reports/

# Download a report
docker compose exec minio mc cp local/reports/<report-id>.pdf ./
```

---

## Seed Scripts

The platform includes scripts to populate the database with required data.

### WCAG Criteria Seed

Seeds all 50 WCAG 2.1 Level A & AA success criteria:

```bash
# Via Makefile
make seed-wcag

# Or directly
docker compose exec api python -m scripts.seed_wcag
```

### Development User Seed

Creates a dev user and organisation:

```bash
# Via Makefile
make seed-dev

# Or directly
docker compose exec api python -m scripts.seed_dev
```

Creates:

- **User**: `dev@example.com` with Firebase UID `dev-user-uid`
- **Organisation**: "Dev Org"
- **Role**: OWNER

### Run All Seeds

```bash
make seed
```

---

## Project Structure

```
accessibility-platform/
├── backend/              # FastAPI application
│   ├── api/              # API routes
│   │   └── v1/           # Version 1 endpoints
│   │       ├── health.py       # Health check
│   │       ├── auth.py         # Auth endpoints
│   │       └── evaluations.py  # Evaluation CRUD
│   ├── core/             # Config, auth, logging
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic schemas
│   ├── scripts/          # Seed scripts
│   ├── tasks/            # Celery background tasks
│   └── alembic/          # Database migrations
├── frontend/             # Vue 3 application
│   └── src/
│       ├── components/   # Reusable UI components
│       ├── pages/        # Route pages
│       ├── stores/       # Pinia state stores
│       ├── router/       # Vue Router config
│       └── lib/          # API, auth utilities
├── nginx/                # Reverse proxy configs
├── .env                  # Environment variables
├── docker-compose.yml    # Production compose
├── docker-compose.dev.yml # Dev overrides
└── Makefile              # Development commands
```

---

## Troubleshooting

### Common Issues

#### Containers Not Starting

**Symptoms**: `make dev` hangs or containers keep restarting

**Solution**:

```bash
# Stop everything and clean up
make down
docker system prune -f

# Restart
make dev
```

#### Port Conflicts

**Symptoms**: `bind: address already in use`

**Solution**:

```bash
# Find what's using the port (e.g., 80)
sudo lsof -i :80

# Kill the process or stop the service
sudo kill <PID>

# Ports used by this project:
# 80 (nginx), 5173 (frontend), 8000 (api), 5432 (postgres)
# 6379 (redis), 9000-9001 (minio), 9099/8080/4000 (firebase)
```

#### PostgreSQL Healthcheck Fails

**Symptoms**: `a11y_postgres` container stuck in "starting" state

**Solution**:

```bash
# Check postgres logs
docker compose logs postgres

# If database doesn't exist, reset:
make reset-db
```

#### API Returns 500 Internal Server Error

**Symptoms**: API calls fail with 500 error

**Solution**:

```bash
# Check API logs for actual error
docker compose logs api --tail=50

# Common causes:
# - Missing migrations: make migrate
# - Missing seeds: make seed
# - Database connection: check postgres is healthy
```

#### "Not authenticated" on All Requests

**Symptoms**: 401 error even with token

**Solution**:

```bash
# Verify ENV=development in .env
grep ENV .env

# Ensure you're using the correct token
curl -H "Authorization: Bearer dev-bypass-token-local-only" \
  -X POST http://localhost/api/v1/auth/me
```

#### Nginx Container Crashes After Restart

**Symptoms**: `a11y_nginx` exits immediately, network error in logs

**Solution**:

```bash
# Remove stale container and recreate
docker rm -f a11y_nginx
docker network prune -f
docker compose up -d nginx
```

#### Frontend Shows Blank Page

**Symptoms**: http://localhost shows white screen

**Solution**:

```bash
# Check frontend logs
docker compose logs frontend

# Verify Vite is running
curl -s http://localhost:5173 | head -5

# If Vite not running, restart frontend
docker compose restart frontend
```

#### Database Reset Required

**Symptoms**: Migration errors, schema conflicts

**Solution**:

```bash
# Full reset (WARNING: destroys all data)
make reset-db

# Or manually:
docker compose down -v  # Remove volumes
make dev                # Fresh start
```

#### Missing WCAG Criteria or Dev User

**Symptoms**: Empty dropdowns, no default user

**Solution**:

```bash
# Run seed scripts manually
make seed

# Or individually:
docker compose exec api python -m scripts.seed_wcag
docker compose exec api python -m scripts.seed_dev
```

### Debug Commands

```bash
# Check all container status
docker ps -a | grep a11y_

# View specific container logs
docker compose logs -f api
docker compose logs -f postgres
docker compose logs -f nginx

# Enter container shell
docker compose exec api bash
docker compose exec postgres psql -U a11y -d accessibility_db

# Check database tables
docker compose exec postgres psql -U a11y -d accessibility_db -c "\dt"

# Check database row counts
docker compose exec postgres psql -U a11y -d accessibility_db -c "
  SELECT 'users' as table_name, COUNT(*) FROM users
  UNION ALL SELECT 'organisations', COUNT(*) FROM organisations
  UNION ALL SELECT 'evaluation_projects', COUNT(*) FROM evaluation_projects
  UNION ALL SELECT 'wcag_criterion', COUNT(*) FROM wcag_criterion;
"

# Test API inside container
docker compose exec api curl http://localhost:8000/api/v1/health

# Rebuild without cache
docker compose build --no-cache api
```

### Getting Help

1. Check container logs: `docker compose logs <service>`
2. Check API docs: http://localhost/api/v1/docs
3. Verify `.env` configuration matches `.env.example`
4. Ensure Docker Desktop is running with sufficient resources (4GB+ RAM)

---

## Next Steps

After successful setup:

1. **Explore API**: Open http://localhost/api/v1/docs
2. **Create Evaluation**: Use the Swagger UI or curl commands above
3. **Check Frontend**: Navigate to http://localhost
4. **Review Code**: Start with `backend/api/v1/evaluations.py`
