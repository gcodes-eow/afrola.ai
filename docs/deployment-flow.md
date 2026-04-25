docs/deployment-flow.md

# Deployment Flow — Afrola.ai (Hetzner + Appliku)

## Purpose
Define the complete deployment process for Afrola.ai using Hetzner Cloud for infrastructure and Appliku for automated deployment, providing a production-ready environment with optimal price-performance ratio.

## Overview
Local Code → GitHub → Appliku → Hetzner → Docker → Production
↓ ↓ ↓ ↓ ↓ ↓
Commit Push Auto- Server Container Live App
Trigger Deploy Provision Build

## Architecture Components

| Component | Service | Purpose |
|-----------|---------|---------|
| Code Repository | GitHub | Source control, versioning |
| CI/CD Platform | Appliku | Automated builds, deployments |
| Cloud Infrastructure | Hetzner Cloud | Virtual servers, object storage |
| Container Runtime | Docker | Application isolation |
| Process Manager | Gunicorn | Django WSGI server |
| Reverse Proxy | Nginx | SSL, static files, load balancing |
| Database | PostgreSQL | Production data persistence |
| Cache/Queue | Redis | Celery broker, caching |
| Task Queue | Celery | Async processing |
| SSL | Let's Encrypt | HTTPS certificates |

## Prerequisites

### Accounts Needed
- [ ] GitHub account (free)
- [ ] Hetzner Cloud account (€20 free credit for new users)
- [ ] Appliku account (14-day free trial)

### Local Setup
- [ ] Git installed and configured
- [ ] Docker installed locally (for testing)
- [ ] All code committed to GitHub repository

## Deployment Steps

### Phase 1: Initial Setup (Day 1)

#### 1.1 GitHub Repository Setup

# Navigate to your project
cd /mnt/c/Users/Owere/Desktop/afrola

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Afrola.ai Django application"

# Create repository on GitHub via web UI or CLI
gh repo create afrola --public --source=. --remote=origin --push

# Or add remote manually
git remote add origin https://github.com/gcodes-eow/afrolapy
git branch -M main
git push -u origin main

1.2 Hetzner Cloud Account Setup

Sign up for Hetzner Cloud:

Visit https://www.hetzner.com/cloud

Click "Register" and create account

Verify email and add payment method

You'll receive €20 free credit

Create SSH Key:

# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/afrola_deploy

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/afrola_deploy

# Copy public key for Hetzner
cat ~/.ssh/afrola_deploy.pub
Add SSH Key to Hetzner:

Go to Hetzner Cloud Console

Click "Security" → "SSH Keys"

Click "Add SSH Key"

Paste your public key

Name it "Afrola Deploy Key"

1.3 Appliku Account Setup

Sign up for Appliku:

Visit https://appliku.com

Click "Start Free Trial" (14 days)

Sign in with GitHub

Connect GitHub:

In Appliku dashboard, go to "GitHub Integration"

Click "Install Appliku on GitHub"

Select your account and repositories

Grant access to your afrola repository

Connect Hetzner:

In Appliku, go to "Cloud Providers"

Click "Add Provider" → "Hetzner"

Get Hetzner API Token:

Go to Hetzner Cloud Console

Click your avatar → "API Tokens"

Click "Generate API Token"

Copy token (save it securely)

Paste token in Appliku

Test connection

Phase 2: Server Provisioning (Day 1-2)

2.1 Create Hetzner Server via Appliku
Server Specifications Recommended:

Tier	vCPU	RAM	Storage	Monthly	Best For
Development	2	4GB	40GB	€4.51	Testing, low traffic
Production (Start)	2	8GB	80GB	€8.81	Launch with ~1000 users
Production (Scale)	4	16GB	160GB	€17.61	5000+ users
For Afrola.ai launch, start with:

Type: CX22 (2 vCPU, 4GB RAM) - €4.51/month

OS: Ubuntu 22.04

Location: Nuremberg (Germany) or Ashburn (US)

Volume: 40GB + optional 10GB volume for media

Create Server in Appliku:

Go to "Servers" → "Create Server"

Select provider: Hetzner

Choose server type: CX22

Select location closest to your users

Choose OS: Ubuntu 22.04

Select your SSH key

Click "Create Server"

Alternative: Manual Hetzner Server Creation

# Using hcloud CLI (install first)
hcloud server create --name afrola-app \
  --type cx22 \
  --image ubuntu-22.04 \
  --location nbg1 \
  --ssh-key ~/.ssh/afrola_deploy.pub
2.2 Configure DNS
Add DNS Records (use your domain provider):

Type    Name     Value
A       @        <your-server-ip>
A       www      <your-server-ip>
CNAME   api      @
CNAME   admin    @
Get server IP:

# Via Hetzner console
# Or SSH to server
ssh root@<server-ip>
Phase 3: Application Configuration (Day 2)
3.1 Prepare Environment Variables
Create production .env file in your repository root:

# Save as .env.production (don't commit .env!)
cat > .env.production << 'EOF'
# Django
DJANGO_SECRET_KEY=<generate-secure-key>
DEBUG=False
ALLOWED_HOSTS=<your-domain.com>,www.<your-domain.com>,<server-ip>

# Database (will be set by Appliku)
DATABASE_URL=postgresql://...

# Redis (will be set by Appliku)
REDIS_URL=redis://...

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Email
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@afrola.ai

# Stripe
STRIPE_PUBLIC_KEY=<stripe-pk-live>
STRIPE_SECRET_KEY=<stripe-sk-live>
STRIPE_WEBHOOK_SECRET=<webhook-secret>

# Frontend
FRONTEND_URL=https://<your-domain.com>
BACKEND_URL=https://api.<your-domain.com>

# File Upload
MAX_UPLOAD_SIZE_MB=500
ALLOWED_AUDIO_TYPES=mp3,wav,m4a,ogg,flac
ALLOWED_VIDEO_TYPES=mp4,avi,mov,mkv,webm

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000

# Logging
LOG_LEVEL=INFO
DJANGO_LOG_LEVEL=INFO
EOF
Generate secure secret key:

bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
3.2 Create Production Settings
Create backend/config/settings_production.py:

python
from .settings import *
import dj_database_url
import os

# Security
DEBUG = False
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': dj_database_url.config(default=os.environ['DATABASE_URL'])
}

# Cache - Use Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ['REDIS_URL'],
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'}
    }
}

# Static & Media
STATIC_ROOT = '/app/staticfiles'
MEDIA_ROOT = '/app/media'

# Use S3 for media files (recommended)
if os.environ.get('AWS_ACCESS_KEY_ID'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'eu-central-1')

# Logging
LOGGING['handlers']['file']['filename'] = '/app/logs/afrola.log'

# Security Headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS
CORS_ALLOWED_ORIGINS = [os.environ.get('FRONTEND_URL', '')]
CORS_ALLOW_CREDENTIALS = True
3.3 Create Dockerfile
Create Dockerfile in project root:

dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    ffmpeg \
    libsndfile1 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY ai/ ./ai/
COPY scripts/ ./scripts/

WORKDIR /app/backend

# Collect static files
RUN python manage.py collectstatic --noinput --settings=config.settings_production

# Run with gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync"]
3.4 Create Celery Dockerfile
Create Dockerfile.celery:

dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ai/ ./ai/

WORKDIR /app/backend

CMD ["celery", "-A", "config", "worker", "--loglevel=info", "--concurrency=2"]
3.5 Create docker-compose.prod.yml
yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=afrola
      - POSTGRES_USER=afrola
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U afrola"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - static_volume:/app/backend/staticfiles
      - media_volume:/app/backend/media
      - logs_volume:/app/backend/logs
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings_production
      - DATABASE_URL=postgresql://afrola:${DB_PASSWORD}@postgres:5432/afrola
      - REDIS_URL=redis://redis:6379
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - FRONTEND_URL=${FRONTEND_URL}
      - STRIPE_PUBLIC_KEY=${STRIPE_PUBLIC_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"

  celery:
    build:
      context: .
      dockerfile: Dockerfile.celery
    volumes:
      - media_volume:/app/backend/media
      - logs_volume:/app/backend/logs
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings_production
      - DATABASE_URL=postgresql://afrola:${DB_PASSWORD}@postgres:5432/afrola
      - REDIS_URL=redis://redis:6379
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.celery
    command: celery -A config beat --loglevel=info
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings_production
      - DATABASE_URL=postgresql://afrola:${DB_PASSWORD}@postgres:5432/afrola
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  nginx:
    image: nginx:alpine
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/static:ro
      - media_volume:/media:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
  logs_volume:
Phase 4: Appliku Deployment (Day 2-3)
4.1 Create App in Appliku
In Appliku dashboard, click "Create App"

Select GitHub repository: yourusername/afrola

App name: afrola

Branch: main

Build type: Dockerfile

Click "Create App"

4.2 Configure Environment Variables
In Appliku, go to App → Settings → Environment Variables:

bash
# Required
DJANGO_SECRET_KEY=<your-secret-key>
DB_PASSWORD=<strong-password>

# Optional (add as needed)
STRIPE_PUBLIC_KEY=
STRIPE_SECRET_KEY=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
4.3 Configure Services
Add PostgreSQL:

In Appliku, go to "Add-ons"

Click "Create PostgreSQL"

Name: afrola-db

Plan: Micro (~$5-7/month, or free tier)

Click "Create"

Link to your app

Add Redis:

In Add-ons, click "Create Redis"

Name: afrola-redis

Plan: Micro (~$3-5/month)

Click "Create"

Link to your app

4.4 Configure Domains
In Appliku, go to App → Domains

Add your domain: afrola.ai

Add www.afrola.ai

Appliku will provide DNS records to add

Add DNS records at your domain registrar:

Type    Name    Value
A       @       <appliku-provided-ip>
CNAME   www     @
4.5 Deploy
In Appliku, click "Deploy"

Select branch: main

Click "Deploy Now"

Watch build logs in real-time

First deployment takes 5-10 minutes:

Building Docker images

Installing dependencies

Running migrations

Starting services

Phase 5: Post-Deployment Setup (Day 3)
5.1 Create Superuser
bash
# SSH into server
ssh root@<server-ip>

# Run management command
docker exec -it afrola_web_1 python manage.py createsuperuser
5.2 Configure SSL (if not auto-configured)
If SSL not automatically configured:

# Install certbot on server
apt update && apt install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d afrola.ai -d www.afrola.ai
5.3 Configure Backups
Database Backup Cron:

# On server, create backup script
cat > /etc/cron.daily/afrola-backup << 'EOF'
#!/bin/bash
docker exec afrola_postgres_1 pg_dump -U afrola afrola > /backups/afrola-$(date +%Y%m%d).sql
# Upload to S3 or Hetzner Storage Box

chmod +x /etc/cron.daily/afrola-backup
Media Files Backup:
Consider using Hetzner Storage Box ($3.29/month for 1TB) for backups.

5.4 Set Up Monitoring
Uptime Monitoring (free):

UptimeRobot: https://uptimerobot.com (free tier: 50 monitors)

Add monitor: https://afrola.ai

Error Tracking (free tier):

Sentry: https://sentry.io (free: 5k errors/month)


# Add to requirements.txt
sentry-sdk==1.40.0

# Add to settings_production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
)
5.5 Configure Logging
bash
# Create log rotation
cat > /etc/logrotate.d/afrola << 'EOF'
/var/log/afrola/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
}

Phase 6: Scaling & Optimization (As Needed)

6.1 When to Scale
Consider upgrading when:

CPU consistently >70%

Memory consistently >80%

Response time >500ms

Daily active users >500

Scale options:

Vertical Scaling: Upgrade Hetzner server type

CX22 (2 vCPU/4GB) → CX32 (4 vCPU/8GB) → CX42 (8 vCPU/16GB)

Horizontal Scaling: Add separate workers

Dedicated Celery worker server

Dedicated database server

6.2 Add Object Storage for Media
Hetzner Storage Box (€3.29/month for 1TB):

# Mount Storage Box to /mnt/afrola-media
# Update Docker volume mount
Or use S3-compatible:

# docker-compose.prod.yml
volumes:
  media:
    driver: local
    driver_opts:
      type: nfs
      o: addr=<storage-box-ip>,rw
      device: :/<path>

6.3 Set Up CDN
Hetzner CDN (per GB pricing):

Create Storage Box bucket

Enable CDN in Hetzner console

Update settings.py:

python
AWS_S3_CUSTOM_DOMAIN = '<cdn.afrola.ai>'
Cost Breakdown
Service	Development	Production (Launch)	Production (Scale)
Hetzner Server (CX22)	€4.51	€4.51	-
Hetzner Server (CX32)	-	-	€8.81
PostgreSQL (Appliku)	€0 (free tier)	€5	€15
Redis (Appliku)	€0 (free tier)	€3	€5
Storage Box (1TB)	-	€3.29	€3.29
Appliku	€0 (trial 14d)	$14	$14
Domain	€10/year	€10/year	€10/year
Monthly Total	€4.51	~€30	~€45
Troubleshooting
Common Issues
Issue: Deployment fails with "Cannot connect to postgres"

bash
# Solution: Check database is healthy
docker logs afrola_postgres_1
# Ensure database service started before web
Issue: Celery tasks not executing

bash
# Check celery logs
docker logs afrola_celery_1
# Verify Redis connection
docker exec afrola_redis_1 redis-cli ping
Issue: Static files not loading

bash
# Re-collect static files
docker exec afrola_web_1 python manage.py collectstatic --noinput
# Check nginx configuration
docker exec afrola_nginx_1 nginx -t
Issue: Out of memory during build

bash
# Add swap space on server
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
Verification Checklist
GitHub repository connected to Appliku

Hetzner server provisioned

Environment variables configured

Database created and connected

Redis created and connected

First deployment successful

SSL certificate installed

Domain resolves to application

Django admin accessible

Static files load correctly

File upload works

Celery tasks execute

Email sending works

Backups configured

Monitoring set up

Logging configured

Useful Commands
bash
# SSH into server
ssh root@<server-ip>

# Check all containers
docker ps

# View logs
docker logs -f afrola_web_1
docker logs -f afrola_celery_1

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Run migrations
docker exec afrola_web_1 python manage.py migrate

# Django shell
docker exec -it afrola_web_1 python manage.py shell

# Backup database
docker exec afrola_postgres_1 pg_dump -U afrola afrola > backup.sql

# Monitor resources
htop
docker stats
Related Documentation
docs/database-schema.md - Production database setup

docs/celery-queue-flow.md - Celery in production

docs/subscription-flow.md - Stripe webhooks

docs/api-rest-flow.md - API rate limiting