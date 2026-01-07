#!/bin/bash
# =============================================================================
# KAVRO - One-Click EC2 Deployment Script
# =============================================================================
# Just run: sudo ./deploy-ec2.sh
# Everything happens automatically - Docker, PostgreSQL, Redis, Nginx, HTTPS
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# CONFIGURATION (auto-generated, no need to change)
# -----------------------------------------------------------------------------
DOMAIN="kavro.duckdns.org"
DUCKDNS_TOKEN="PASTE_YOUR_TOKEN_HERE"  # Get from duckdns.org (optional)
DB_PASSWORD="$(openssl rand -base64 24)"
SECRET_KEY="$(openssl rand -hex 32)"
EMAIL="admisure215@gmail.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Check root
if [ "$EUID" -ne 0 ]; then
  error "Run as root: sudo ./deploy-ec2.sh"
fi

echo ""
echo "=============================================="
echo "   KAVRO - One-Click Deployment"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# STEP 1: Install Docker (auto-detect OS)
# -----------------------------------------------------------------------------
log "Installing Docker..."

if command -v docker &> /dev/null; then
    log "Docker already installed"
else
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    fi

    if [ "$OS" = "amzn" ]; then
        # Amazon Linux
        yum update -y -q
        yum install -y -q docker
        systemctl start docker
        systemctl enable docker
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        # Ubuntu/Debian
        apt update -qq
        apt install -y -qq docker.io
        systemctl start docker
        systemctl enable docker
    else
        # Generic install
        curl -fsSL https://get.docker.com | sh
        systemctl start docker
        systemctl enable docker
    fi
fi

log "Docker ready"

# -----------------------------------------------------------------------------
# STEP 2: Install Docker Compose
# -----------------------------------------------------------------------------
log "Installing Docker Compose..."

if command -v docker-compose &> /dev/null; then
    log "Docker Compose already installed"
else
    curl -sL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

log "Docker Compose ready"

# -----------------------------------------------------------------------------
# STEP 3: Install Nginx
# -----------------------------------------------------------------------------
log "Installing Nginx..."

if [ "$OS" = "amzn" ]; then
    amazon-linux-extras install nginx1 -y -q 2>/dev/null || yum install -y -q nginx
elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt install -y -qq nginx
else
    yum install -y -q nginx 2>/dev/null || apt install -y -qq nginx
fi

systemctl start nginx
systemctl enable nginx

log "Nginx ready"

# -----------------------------------------------------------------------------
# STEP 4: Create Kavro directory and files
# -----------------------------------------------------------------------------
log "Setting up Kavro..."

mkdir -p /opt/kavro
cd /opt/kavro

# Create .env
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://kavro:${DB_PASSWORD}@db:5432/kavro
POSTGRES_USER=kavro
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=kavro
SECRET_KEY=${SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=1440
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  api:
    image: ashishkrshaw/kavro-api:latest
    container_name: kavro-api
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=redis://redis:6379
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    networks:
      - kavro

  db:
    image: postgres:14-alpine
    container_name: kavro-db
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kavro"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: always
    networks:
      - kavro

  redis:
    image: redis:7-alpine
    container_name: kavro-redis
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: always
    networks:
      - kavro

volumes:
  pgdata:
  redisdata:

networks:
  kavro:
COMPOSE

log "Config files created"

# -----------------------------------------------------------------------------
# STEP 5: Start containers
# -----------------------------------------------------------------------------
log "Pulling Docker images (this takes 1-2 minutes)..."
docker-compose pull

log "Starting services..."
docker-compose up -d

log "Waiting for services..."
sleep 20

# Check health
for i in {1..10}; do
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        log "API is running!"
        break
    fi
    sleep 3
done

# -----------------------------------------------------------------------------
# STEP 6: Configure Nginx
# -----------------------------------------------------------------------------
log "Configuring Nginx proxy..."

cat > /etc/nginx/conf.d/kavro.conf << 'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

# Remove default configs
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

nginx -t && systemctl reload nginx

log "Nginx configured"

# -----------------------------------------------------------------------------
# STEP 7: Setup HTTPS (optional - needs domain)
# -----------------------------------------------------------------------------
if [ "$DOMAIN" != "kavro.duckdns.org" ] || [ "$DUCKDNS_TOKEN" != "PASTE_YOUR_TOKEN_HERE" ]; then
    log "Setting up HTTPS for $DOMAIN..."
    
    # Install certbot
    if [ "$OS" = "amzn" ]; then
        amazon-linux-extras install epel -y 2>/dev/null || true
        yum install -y -q certbot python-certbot-nginx 2>/dev/null || yum install -y -q certbot python3-certbot-nginx
    else
        apt install -y -qq certbot python3-certbot-nginx
    fi
    
    # Update nginx config with domain
    cat > /etc/nginx/conf.d/kavro.conf << EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    nginx -t && systemctl reload nginx
    
    # Update DuckDNS
    if [ "$DUCKDNS_TOKEN" != "PASTE_YOUR_TOKEN_HERE" ]; then
        curl -s "https://www.duckdns.org/update?domains=${DOMAIN%.duckdns.org}&token=${DUCKDNS_TOKEN}&ip="
        log "DuckDNS updated"
    fi
    
    # Get certificate
    certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --email ${EMAIL} --redirect || warn "HTTPS setup failed, try manually: certbot --nginx -d ${DOMAIN}"
fi

# -----------------------------------------------------------------------------
# STEP 8: Create helper scripts
# -----------------------------------------------------------------------------
cat > /opt/kavro/logs.sh << 'EOF'
#!/bin/bash
cd /opt/kavro && docker-compose logs -f api
EOF
chmod +x /opt/kavro/logs.sh

cat > /opt/kavro/status.sh << 'EOF'
#!/bin/bash
cd /opt/kavro
echo "=== Containers ==="
docker-compose ps
echo ""
echo "=== Health ==="
curl -s http://localhost:8000/health
echo ""
EOF
chmod +x /opt/kavro/status.sh

cat > /opt/kavro/update.sh << 'EOF'
#!/bin/bash
cd /opt/kavro
docker-compose pull
docker-compose up -d
echo "Updated!"
EOF
chmod +x /opt/kavro/update.sh

# -----------------------------------------------------------------------------
# DONE
# -----------------------------------------------------------------------------
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com)

echo ""
echo "=============================================="
echo -e "${GREEN}   DEPLOYMENT COMPLETE!${NC}"
echo "=============================================="
echo ""
echo "Your API is live at:"
echo ""
echo -e "  ${GREEN}http://${PUBLIC_IP}${NC}"
echo -e "  ${GREEN}http://${PUBLIC_IP}/docs${NC}  (API Docs)"
echo -e "  ${GREEN}http://${PUBLIC_IP}/health${NC}"
echo ""
if [ "$DOMAIN" != "kavro.duckdns.org" ] || [ "$DUCKDNS_TOKEN" != "PASTE_YOUR_TOKEN_HERE" ]; then
    echo -e "  ${GREEN}https://${DOMAIN}${NC}"
    echo -e "  ${GREEN}https://${DOMAIN}/docs${NC}"
fi
echo ""
echo "Commands:"
echo "  /opt/kavro/status.sh  - Check status"
echo "  /opt/kavro/logs.sh    - View logs"
echo "  /opt/kavro/update.sh  - Update Kavro"
echo ""
echo "Secrets saved in: /opt/kavro/.env"
echo ""
