# Developer Setup Guide

Quick setup guide for local development.

## Prerequisites

- Docker Desktop (running)
- Git
- Node.js 20+ (for Firebase emulator)

## Initial Setup

1. **Clone and configure**

   ```bash
   git clone <repository-url>
   cd accessibility-platform
   cp .env.example .env
   ```

2. **Install Firebase CLI** (for emulator)

   ```bash
   npm install
   npm install -g firebase-tools
   ```

3. **Start all services**

   ```bash
   make dev
   ```

4. **Verify setup**
   ```bash
   curl http://localhost/api/v1/health
   ```

## Daily Usage

### Using Makefile (Recommended)

**Start dev mode** (after laptop restart):

```bash
make dev
```

**Start production mode**:

```bash
make up
```

**Stop services**:

```bash
make down
```

**View logs**:

```bash
make logs
```

**Run migrations**:

```bash
make migrate
```

**Reset database** (destroys all data):

```bash
make reset-db
```

**Shell access**:

```bash
make shell-api  # API container bash
make shell-db   # PostgreSQL psql
```

### Without Makefile

**Start dev mode**:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Start in background**:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**View logs**:

```bash
docker compose logs -f
docker compose logs -f api      # API only
docker compose logs -f frontend # Frontend only
```

## Access Points

### Application

- **Frontend**: http://localhost
- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost/api/v1/docs
- **API Docs (ReDoc)**: http://localhost/api/v1/redoc

### Infrastructure

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **PostgreSQL**: localhost:5432 (a11y/a11ypass)
- **Redis**: localhost:6379

### Firebase Emulator

- **Emulator UI**: http://127.0.0.1:4000
- **Auth Emulator**: http://127.0.0.1:9099 (UI: http://127.0.0.1:4000/auth)
- **Firestore Emulator**: http://127.0.0.1:8080 (UI: http://127.0.0.1:4000/firestore)

**Start emulator**:

```bash
firebase emulators:start
```

## Development Features

- **Hot reload** enabled for both frontend and backend
- Code changes auto-reflect without restart
- Frontend: Vite HMR
- Backend: Uvicorn auto-reload
- Firebase emulator for local auth testing

## Project Structure

```
accessibility-platform/
├── backend/          # FastAPI application
│   ├── api/         # API routes
│   ├── core/        # Config, auth, logging
│   ├── db/          # Database setup
│   ├── tasks/       # Celery tasks
│   └── alembic/     # Database migrations
├── frontend/        # Vue 3 application
├── nginx/           # Reverse proxy configs
├── .env             # Environment variables
└── Makefile         # Development commands
```

## Troubleshooting

**Containers not starting?**

```bash
make down
make dev
```

**Port conflicts?**

```bash
make down
# Check ports: 80, 5173, 8000, 5432, 6379, 9000, 9001, 9099, 8080, 4000, 4400, 4500, 9150
```

**Database issues**:

```bash
make reset-db  # Full reset with migrations
```

**API not responding**:

```bash
docker compose logs api
make shell-api  # Debug inside container
```

## Test api

```bash
curl http://localhost/api/v1/health
```
