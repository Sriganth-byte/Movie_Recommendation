import os
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

import pandas as pd
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from loader import load_catalog
import recommender


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("cinimatch.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_catalog()
    logger.info("CiniMatch catalog is ready")
    yield


class PersonalRecommendRequest(BaseModel):
    movie: Optional[str] = Field(default=None, max_length=200)
    genres: list[str] = Field(default_factory=list, max_length=12)
    rating: float = Field(default=6.5, ge=0, le=10)
    mood: Optional[str] = Field(default=None, max_length=40)
    yearFrom: int = Field(default=2000, ge=1900, le=2100)
    yearTo: int = Field(default=2100, ge=1900, le=2100)

    @field_validator("genres")
    @classmethod
    def clean_genres(cls, value):
        return [genre.strip() for genre in value if isinstance(genre, str) and genre.strip()]

    @field_validator("movie", "mood")
    @classmethod
    def clean_optional_text(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None


class MetadataResponse(BaseModel):
    genres: list[str]
    moods: list[str]
    yearMin: int
    yearMax: int
    movieCount: int
    datasetSha256: str


MovieResponse = dict[str, Any]


app = FastAPI(
    title="CiniMatch API",
    version="1.0.0",
    description="Movie discovery and recommendation API.",
    lifespan=lifespan,
)

default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", default_origins).split(",")
    if origin.strip()
]
if not allowed_origins:
    logger.warning("CORS_ORIGINS resolved to an empty list — all cross-origin requests will be blocked")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.4f}"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def records(frame):
    return frame.to_dict("records") if isinstance(frame, pd.DataFrame) else []


@app.get("/health")
def health():
    return {"status": "ok", "movies": len(load_catalog().df)}


@app.get("/")
def root():
    return {"message": "CiniMatch backend is running"}


@app.get("/metadata", response_model=MetadataResponse)
def metadata():
    return recommender.get_metadata()


@app.get("/trending", response_model=list[MovieResponse])
def trending(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    return records(recommender.get_trending(offset, limit))


@app.get("/genre/{genre}", response_model=list[MovieResponse])
def movies_by_genre(
    genre: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    return records(recommender.recommend_by_genres([genre], offset, limit))


@app.get("/search", response_model=list[MovieResponse])
def search_movies(
    q: str = Query(..., min_length=2, max_length=100),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    return records(recommender.search_movies(q, offset, limit))


@app.post("/personal-recommend", response_model=list[MovieResponse])
def personal_recommend_endpoint(
    payload: PersonalRecommendRequest,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    return records(
        recommender.personal_recommend(
            movie=payload.movie,
            genres=payload.genres,
            rating=payload.rating,
            mood=payload.mood,
            yearFrom=payload.yearFrom,
            yearTo=payload.yearTo,
            offset=offset,
            limit=limit,
        )
    )


@app.get("/movies/{imdb_id}/similar", response_model=list[MovieResponse])
def similar_movies(
    imdb_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=20),
):
    return records(recommender.recommend_similar(imdb_id, offset, limit))


@app.get("/movies/{imdb_id}/credits")
def movie_credits(imdb_id: str):
    return recommender.get_movie_credits(imdb_id)
