#!/usr/bin/env bash
#
# Server Setup Script for WCAG Accessibility Evaluation Platform
# Run this ONCE on a fresh Ubuntu 22.04 VPS to prepare it for deployment
#
# Usage: curl -sSL https://raw.githubusercontent.com/antaripdebgupta/accessibility-platform/main/deploy/setup.sh | bash
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  log_error "Please run as root (use sudo)"
  exit 1
fi

log_info "=== WCAG Accessibility Platform - Server Setup ==="
log_info "This will install Docker, configure firewall, and create deployment user"
echo

# Update package index
log_info "Updating package index..."
apt-get update -qq

# Install prerequisites
log_info "Installing prerequisites..."
apt-get install -y -qq \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  git \
  ufw

# Install Docker
if ! command -v docker &> /dev/null; then
  log_info "Installing Docker..."

  # Add Docker's official GPG key
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  # Set up Docker repository
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

  # Install Docker Engine
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  # Start and enable Docker
  systemctl start docker
  systemctl enable docker

  log_info "Docker installed successfully"
else
  log_info "Docker already installed ($(docker --version))"
fi

# Configure UFW firewall
log_info "Configuring firewall..."
ufw --force disable  # Disable first to reset rules
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable
log_info "Firewall configured (SSH, HTTP, HTTPS allowed)"

# Create deploy user
if ! id "deploy" &>/dev/null; then
  log_info "Creating 'deploy' user..."
  useradd -m -s /bin/bash deploy
  usermod -aG docker deploy
  log_info "User 'deploy' created and added to docker group"
else
  log_info "User 'deploy' already exists"
  usermod -aG docker deploy
fi

# Create app directory
log_info "Creating application directory..."
mkdir -p /opt/a11y-platform
chown deploy:deploy /opt/a11y-platform
log_info "Created /opt/a11y-platform"

# Configure Docker daemon for production
log_info "Configuring Docker daemon..."
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
systemctl restart docker
log_info "Docker daemon configured"

# Enable automatic security updates
log_info "Enabling automatic security updates..."
apt-get install -y -qq unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
log_info "Automatic security updates enabled"

# Display summary
echo
log_info "Setup Complete"
echo
echo "Docker installed: $(docker --version)"
echo "Docker Compose installed: $(docker compose version)"
echo "Firewall configured (ports 22, 80, 443)"
echo "User 'deploy' created with Docker access"
echo "App directory created at /opt/a11y-platform"
echo
log_info "Next steps:"
echo "1. Switch to deploy user: su - deploy"
echo "2. Clone repository: cd /opt/a11y-platform && git clone <repo-url> ."
echo "3. Configure environment: cp .env.prod.example .env.prod && nano .env.prod"
echo "4. Get SSL certificate: sudo bash deploy/ssl.sh yourdomain.com"
echo "5. Deploy: bash deploy/deploy.sh"
echo
log_warn "Remember to:"
echo "  - Set up DNS A record pointing to this server's IP"
echo "  - Upload Firebase service account key to /opt/a11y-platform/secrets/"
echo "  - Configure SMTP settings in .env.prod for email notifications"
echo
