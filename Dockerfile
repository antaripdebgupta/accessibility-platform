# Root Dockerfile for Render compatibility
# This Dockerfile builds the backend when Render auto-detects Docker at repo root.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps required by asyncpg, WeasyPrint, Playwright
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       libpango-1.0-0 \
       libpangocairo-1.0-0 \
       libgdk-pixbuf-2.0-0 \
       libffi-dev \
       shared-mime-info \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for caching
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Playwright and browsers (required by the crawler)
RUN pip install playwright==1.44.0 || true
RUN playwright install chromium --with-deps || true

# Copy backend source
COPY backend /app

# Expose port used by Uvicorn
EXPOSE 8000

# Default command — Render web service will override this if it uses a startCommand
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
