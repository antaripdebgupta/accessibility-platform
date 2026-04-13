#!/usr/bin/env bash
#
# Deployment Script for WCAG Accessibility Evaluation Platform
# Run this on every release to update the application
#
# Usage: bash deploy/deploy.sh
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Change to repository root
cd "$(dirname "$0")/.."

log_info "=== WCAG Accessibility Platform - Deployment ==="
echo

# Step 1: Git pull
log_step "1/7 Pulling latest code from Git..."
git fetch origin
git pull origin main
log_info "Code updated to $(git rev-parse --short HEAD)"

# Step 2: Build images
log_step "2/7 Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache
log_info "Images built successfully"

# Step 3: Stop old containers
log_step "3/7 Stopping old containers..."
docker compose -f docker-compose.prod.yml down
log_info "Old containers stopped"

# Step 4: Start new containers
log_step "4/7 Starting new containers..."
docker compose -f docker-compose.prod.yml up -d
log_info "Containers started"

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Step 5: Run database migrations
log_step "5/7 Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
log_info "Migrations applied"

# Step 6: Seed WCAG criteria
log_step "6/7 Seeding WCAG criteria..."
docker compose -f docker-compose.prod.yml exec -T api python -m scripts.seed_wcag
log_info "WCAG criteria seeded"

# Step 7: Health check
log_step "7/7 Running health check..."
sleep 5
HEALTH=$(curl -s -f http://localhost/api/v1/health || echo "FAIL")
if echo "$HEALTH" | grep -q "ok"; then
  log_info "Health check passed"
else
  log_error "Health check failed"
  log_error "Response: $HEALTH"
  exit 1
fi

# Show running containers
echo
log_info "=== Deployment Complete ==="
echo
log_info "Running containers:"
docker compose -f docker-compose.prod.yml ps
echo
log_info "Application URLs:"
echo "  - Frontend: https://$(hostname -f)"
echo "  - API Docs: https://$(hostname -f)/api/v1/docs"
echo
log_info "View logs: docker compose -f docker-compose.prod.yml logs -f"
log_info "Stop services: docker compose -f docker-compose.prod.yml down"
echo
