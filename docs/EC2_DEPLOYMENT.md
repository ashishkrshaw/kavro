# Deploying Kavro on EC2

Hey! So you want to deploy Kavro on AWS EC2 with HTTPS. I'll walk you through it step by step. We'll use DuckDNS for the free subdomain.

## What We're Building

```
Your Browser
     ↓
https://yourname.duckdns.org (port 443)
     ↓
Nginx (handles SSL)
     ↓
Kavro API (port 8000)
```

## Before You Start

You'll need:
- An AWS EC2 instance (Ubuntu works best)
- A DuckDNS account (free at duckdns.org)

## Part 1: DuckDNS Setup

Go to [duckdns.org](https://www.duckdns.org) and sign in with Google/GitHub.

1. Pick a subdomain name (like `kavro-api`)
2. You'll get: `kavro-api.duckdns.org`
3. Point it to your EC2's public IP
4. Save your DuckDNS **token** (you'll need it later)

That's it for DuckDNS.

## Part 2: EC2 Setup

SSH into your EC2:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### Install Docker

```bash
sudo apt update
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and log back in (so docker works without sudo).

### Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Install Nginx

```bash
sudo apt install nginx -y
```

## Part 3: Run Kavro

Create a folder and go there:

```bash
mkdir ~/kavro
cd ~/kavro
```

### Create the .env file

```bash
nano .env
```

Paste this (change the passwords!):

```
DATABASE_URL=postgresql+asyncpg://kavro:pickastrongpassword@db:5432/kavro
POSTGRES_USER=kavro
POSTGRES_PASSWORD=pickastrongpassword
POSTGRES_DB=kavro
SECRET_KEY=makethisareallylongrandomstring123456789
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

To generate a good secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Create docker-compose.yml

```bash
nano docker-compose.yml
```

Paste this:

```yaml
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
    restart: unless-stopped
    networks:
      - app

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
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app

  redis:
    image: redis:7-alpine
    container_name: kavro-redis
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - app

volumes:
  pgdata:
  redisdata:

networks:
  app:
```

### Start it up

```bash
docker-compose pull
docker-compose up -d
```

Check if it works:
```bash
curl http://localhost:8000/health
```

You should see `{"status":"ok","service":"kavro","version":"1.0.0"}`

## Part 4: Nginx Config

Create nginx config:

```bash
sudo nano /etc/nginx/sites-available/kavro
```

Paste this (change `kavro-api.duckdns.org` to YOUR subdomain):

```nginx
server {
    listen 80;
    server_name kavro-api.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/kavro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Try it:
```bash
curl http://kavro-api.duckdns.org/health
```

## Part 5: HTTPS with Let's Encrypt

This is the easy part. Certbot does everything for you.

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d kavro-api.duckdns.org
```

It'll ask for your email and some yes/no questions. Say yes to redirect HTTP to HTTPS.

Done! Try it:
```bash
curl https://kavro-api.duckdns.org/health
```

## Part 6: Keep DuckDNS Updated

Your EC2 IP might change. Set up auto-update:

```bash
mkdir ~/duckdns
nano ~/duckdns/duck.sh
```

Paste (change YOUR_SUBDOMAIN and YOUR_TOKEN):

```bash
#!/bin/bash
curl -s "https://www.duckdns.org/update?domains=YOUR_SUBDOMAIN&token=YOUR_TOKEN&ip="
```

Make it run every 5 minutes:

```bash
chmod +x ~/duckdns/duck.sh
crontab -e
```

Add this line:
```
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

## You're Done!

Your API is now live at:
- `https://kavro-api.duckdns.org/docs` - API documentation
- `https://kavro-api.duckdns.org/health` - Health check

## If Something Breaks

Check the logs:

```bash
# API logs
docker-compose logs -f api

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

Restart stuff:

```bash
docker-compose restart
sudo systemctl restart nginx
```

## Updating Kavro Later

```bash
cd ~/kavro
docker-compose pull
docker-compose up -d
```

That's it. You're running Kavro with HTTPS on EC2 using DuckDNS. Pretty cool, right?
