# CiniMatch Deployment Guide

## Overview

CiniMatch is a movie recommendation app consisting of:
- **Backend**: FastAPI (Python) serving REST API on port 8000
- **Frontend**: React 19 + Vite, served via Nginx on port 8080
- **Data**: Local files (CSV + Pickle) ~350MB total, loaded into memory at startup

---

## Free Deployment Options

### Option 1: Railway.app (Recommended — $5/mo free credit)

Railway supports Docker-based deployments natively.

1. Push code to GitHub
2. Connect GitHub on [railway.app](https://railway.app)
3. Create a new project → "Deploy from GitHub Repo"
4. Railway auto-detects Dockerfiles
5. Configure environment variables:

```
CORS_ORIGINS=*
DATA_DIR=/app/data
LOG_LEVEL=INFO
```

6. For data persistence, add a **Volume** add-on or use an S3-compatible bucket
7. The frontend auto-builds and serves on Railway's generated URL

**Cost**: Free ($5 credit/month, enough for light usage)

---

### Option 2: Render.com (Free tier with auto-sleep)

Deploy backend and frontend as separate services:

**Backend (Web Service):**
- Root directory: `backend/`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add **Persistent Disk** (free 1GB) for data files

**Frontend (Static Site):**
- Root directory: `frontend/cinimatch/`
- Build: `npm ci && npm run build`
- Publish directory: `build`
- Set env: `VITE_API_BASE_URL=https://your-backend.onrender.com`

**Cost**: Free (services sleep after 15min inactivity)

---

### Option 3: Fly.io (Free shared VMs)

Three free `shared-cpu-1x` VMs with 256MB RAM each.

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy backend
cd backend
fly launch --name cinimatch-backend --region hkg --no-deploy
fly volumes create data --size 1
# Edit fly.toml: set internal_port = 8000, services[0].port = 8000
fly secrets set DATA_DIR=/data CORS_ORIGINS="*"
fly deploy

# Deploy frontend
cd ../frontend/cinimatch
fly launch --name cinimatch-frontend --region hkg --no-deploy
# Edit fly.toml: set internal_port = 80
fly secrets set VITE_API_BASE_URL="https://cinimatch-backend.fly.dev"
fly deploy
```

**Cost**: Free (3 VMs, ~256MB RAM each)

---

### Option 4: Self-hosted + Cloudflare Tunnel (100% Free)

Run on any machine (Raspberry Pi, old laptop, cheap VPS):

```bash
# Run with Docker Compose
docker compose up --build -d
```

Expose with Cloudflare Tunnel (unlimited free subdomains):

```bash
# Install cloudflared
# On macOS: brew install cloudflared
# On Linux: download from https://github.com/cloudflare/cloudflared/releases

cloudflared tunnel login
cloudflared tunnel create cinimatch
cloudflared tunnel route dns cinimatch cinimatch.yourdomain.com
cloudflared tunnel run cinimatch --url http://localhost:8080
```

**Cost**: $0 (requires a domain for HTTPS)

---

### Option 5: Vercel + Render (Full stack, all free)

**Frontend on Vercel:**
1. Import `frontend/cinimatch` repo on [vercel.com](https://vercel.com)
2. Set environment variable: `VITE_API_BASE_URL=https://your-render-backend.onrender.com`
3. Vercel auto-detects Vite and deploys

**Backend on Render:**
- Same as Option 2 backend setup

**Cost**: $0

---

## Docker Compose (Local Production)

For running on your own server/VPS:

```bash
# Set environment
cp .env.example .env
# Edit .env with your domain names

# Build and run
docker compose up --build -d

# Monitor logs
docker compose logs -f
```

### docker-compose.yml

```yaml
services:
  backend:
    build:
      context: ./backend
    environment:
      CORS_ORIGINS: ${CORS_ORIGINS:-http://localhost:3000,http://localhost:8080}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend/cinimatch
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL:-http://localhost:8000}
    ports:
      - "8080:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

---

## Data Persistence Strategy

The `backend/data/` directory (~350MB) contains large ML data files. For free tiers with ephemeral storage:

| Provider | Solution |
|----------|----------|
| **Render** | Persistent disk (free 1GB) |
| **Fly.io** | Persistent volume (free 3GB) |
| **Railway** | Volume add-on ($0.10/GB/mo) |
| **VPS** | Direct mount from host |
| **Cloudflare** | R2 bucket + runtime cache |

---

## Post-Deployment Checklist

- [ ] Update `CORS_ORIGINS` with the deployed frontend URL
- [ ] Set `VITE_API_BASE_URL` to the deployed backend URL
- [ ] Verify data files are present and readable
- [ ] Enable HTTPS (Cloudflare Tunnel or Let's Encrypt)
- [ ] Test all API endpoints
- [ ] Monitor memory usage (~500MB+ for data loading)
- [ ] Set up health checks if not using Docker Compose

---

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser    │────▶│  Nginx       │────▶│  FastAPI    │
│  (React SPA) │     │  (Port 80)   │     │  (Port 8000)│
│  Port 8080   │     │              │     │             │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                                          ┌──────▼──────┐
                                          │ Data Files  │
                                          │ (CSV/Pickle)│
                                          │ ~350MB      │
                                          └─────────────┘
```