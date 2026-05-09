# CiniMatch

CiniMatch is a movie discovery app with a FastAPI recommendation backend and a React frontend.

## Features

- Trending, genre, search, similar-movie, credits, and personalized recommendation APIs
- Typed FastAPI request validation
- Recommendation scoring across genre, mood, rating, year, popularity, votes, cast, director, collection, and semantic vectors
- Debounced/cancellable frontend search
- Docker Compose setup for local production-like runs
- Backend and frontend smoke tests

## Project Structure

```text
backend/                  FastAPI app and recommender engine
backend/data/             Local dataset and vector files, ignored by Git
frontend/cinimatch/       React app
docker-compose.yml        Backend + frontend container setup
```

## Required Data Files

Place these files in `backend/data/`:

```text
rich_movies_dataset.csv
movie_vectors.pkl
movie_ids.pkl
title_to_index.pkl
```

## Local Development

Using Docker Compose (recommended):

```bash
docker compose up --build
```

Frontend: `http://localhost:8080`  
Backend: `http://localhost:8000`

Or manually:

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend/cinimatch
npm install
npm start
```

Set `frontend/cinimatch/.env` when the backend URL changes:

```text
REACT_APP_API_BASE_URL=http://127.0.0.1:8000
```

## Production Deployment

### With Docker Compose (any VPS)

```bash
# Set environment variables
export CORS_ORIGINS=https://your-frontend-domain.com
export VITE_API_BASE_URL=https://your-backend-domain.com

# Build and run
docker compose up --build -d
```

### Free Hosting Options

#### Railway (easiest, $5/mo free tier)
1. Push code to GitHub
2. Go to [railway.app](https://railway.app) and connect GitHub
3. Deploy from your repo — Railway detects Dockerfiles
4. Set env vars: `CORS_ORIGINS=*`, `DATA_DIR=/app/data`
5. Upload data files to a persistent volume or S3 bucket

#### Render (free tier with auto-sleep)
- **Backend**: Web Service → `./backend`, start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Frontend**: Static Site → `./frontend/cinimatch`, build: `npm ci && npm run build`, publish: `build`
- Add persistent disk (free up to 1GB) for data files

#### Fly.io (3 free shared VMs)
```bash
# Backend
cd backend
fly launch --name cinimatch-backend
fly secrets set DATA_DIR=/data CORS_ORIGINS="https://cinimatch-frontend.fly.dev"
fly volumes create data --size 1
fly deploy

# Frontend
cd ../frontend/cinimatch
fly launch --name cinimatch-frontend
fly deploy
```

#### Self-hosted + Cloudflare Tunnel (completely free)
```bash
# Run locally or on any VPS
docker compose up --build -d

# Expose via Cloudflare Tunnel (free)
cloudflared tunnel create cinimatch
cloudflared tunnel route dns cinimatch yourdomain.com
cloudflared tunnel run --url http://localhost:8080
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,http://localhost:8080` |
| `LOG_LEVEL` | Backend log level | `INFO` |
| `VITE_API_BASE_URL` | Frontend API base URL (build-time) | `http://localhost:8000` |
| `DATA_DIR` | Path to data files | `./backend/data` |

## Validation

```bash
cd backend
pytest
```

```bash
cd frontend/cinimatch
npm run test:ci
npm run build
```

## Deployment Notes

- Configure backend `CORS_ORIGINS` to the deployed frontend URL.
- Configure frontend `VITE_API_BASE_URL` at build time.
- Keep `backend/data/` outside Git and mount it as read-only in production.
- For very high traffic, replace live cosine similarity with a persisted ANN index such as FAISS or HNSWLib.