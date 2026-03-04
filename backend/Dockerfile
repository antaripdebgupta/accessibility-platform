# Accessibility Platform — API Dockerfile
# Production-ready FastAPI service with Python 3.12

FROM python:3.12-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # pip configuration
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # app configuration
    APP_HOME=/app

WORKDIR $APP_HOME

# Install system dependencies required by some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for asyncpg
    libpq-dev \
    # Required for weasyprint PDF generation
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Dependencies stage
FROM base AS dependencies

# Install build tools needed for some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base AS production

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run with gunicorn + uvicorn workers for production
CMD ["gunicorn", "main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--timeout", "120"]
