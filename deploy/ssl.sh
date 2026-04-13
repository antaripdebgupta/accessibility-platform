#!/usr/bin/env bash
#
# SSL Certificate Setup Script using Let's Encrypt
# Run this BEFORE first deployment to get SSL certificates
#
# Usage: sudo bash deploy/ssl.sh yourdomain.com
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  log_error "Please run as root (use sudo)"
  exit 1
fi

# Check if domain provided
if [ $# -eq 0 ]; then
  log_error "Usage: sudo bash deploy/ssl.sh yourdomain.com"
  exit 1
fi

DOMAIN=$1

log_info "=== SSL Certificate Setup for $DOMAIN ==="
echo

# Install certbot
if ! command -v certbot &> /dev/null; then
  log_info "Installing certbot..."
  apt-get update -qq
  apt-get install -y -qq certbot
  log_info "Certbot installed"
else
  log_info "Certbot already installed ($(certbot --version))"
fi

# Check if nginx is running (stop it for standalone mode)
if systemctl is-active --quiet nginx || docker ps | grep -q nginx; then
  log_warn "Nginx is running. Please stop it before running this script."
  log_warn "Run: docker compose -f docker-compose.prod.yml down"
  exit 1
fi

# Get certificate using standalone mode
log_info "Obtaining SSL certificate from Let's Encrypt..."
log_warn "Make sure port 80 is accessible from the internet"
echo

certbot certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --email admin@${DOMAIN} \
  --domains ${DOMAIN}

if [ $? -eq 0 ]; then
  log_info "Certificate obtained successfully"
  log_info "Certificate location: /etc/letsencrypt/live/${DOMAIN}/"
else
  log_error "Failed to obtain certificate"
  log_error "Troubleshooting:"
  echo "  1. Check DNS: dig ${DOMAIN}"
  echo "  2. Check port 80 is open: sudo ufw status"
  echo "  3. Verify domain points to this server's IP"
  exit 1
fi

# Set up auto-renewal
log_info "Setting up automatic renewal..."

# Create renewal hook to reload nginx
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh <<EOF
#!/bin/bash
cd /opt/a11y-platform
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

# Test renewal (dry run)
log_info "Testing renewal process..."
certbot renew --dry-run

# Add cron job for auto-renewal (runs twice daily)
(crontab -l 2>/dev/null; echo "0 0,12 * * * /usr/bin/certbot renew --quiet --deploy-hook '/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh'") | crontab -

log_info "Auto-renewal configured"

# Display summary
echo
log_info "SSL Setup Complete"
echo
echo "Certificate obtained for: $DOMAIN"
echo "Certificate location: /etc/letsencrypt/live/${DOMAIN}/"
echo "Auto-renewal enabled (runs twice daily)"
echo
log_info "Next steps:"
echo "1. Update nginx/nginx.prod.conf with your domain"
echo "2. Run deployment: bash deploy/deploy.sh"
echo
log_warn "Certificate expires in 90 days but will auto-renew"
log_info "Check renewal status: sudo certbot renew --dry-run"
echo
