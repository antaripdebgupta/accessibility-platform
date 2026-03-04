# Accessibility Evaluation Platform

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
