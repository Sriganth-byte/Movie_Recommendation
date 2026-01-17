from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import recommender
import pandas as pd
import os

app = FastAPI(title="CiniMatch API")

# ===================== CORS =====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # add after frontend deploy
        # "https://cinimatch.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== HEALTH =====================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===================== ROOT =====================
@app.get("/")
def root():
    return {"message": "CiniMatch backend is running"}

# ===================== TRENDING =====================
@app.get("/trending")
def trending(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    df = recommender.get_trending(offset, limit)
    return df.to_dict("records") if isinstance(df, pd.DataFrame) else []

# ===================== GENRE =====================
@app.get("/genre/{genre}")
def movies_by_genre(
    genre: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    df = recommender.recommend_by_genres([genre], offset, limit)
    return df.to_dict("records") if isinstance(df, pd.DataFrame) else []

# ===================== SEARCH =====================
@app.get("/search")
def search_movies(
    q: str = Query(..., min_length=2),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    df = recommender.search_movies(q, offset, limit)
    return df.to_dict("records") if isinstance(df, pd.DataFrame) else []

# ===================== PERSONAL RECOMMEND =====================
@app.post("/personal-recommend")
def personal_recommend_endpoint(
    payload: dict = Body(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    df = recommender.personal_recommend(
        movie=payload.get("movie"),
        genres=payload.get("genres"),
        rating=payload.get("rating"),
        mood=payload.get("mood"),
        yearFrom=payload.get("yearFrom"),
        yearTo=payload.get("yearTo"),
        offset=offset,
        limit=limit,
    )
    return df.to_dict("records") if isinstance(df, pd.DataFrame) else []

# ===================== SIMILAR =====================
@app.get("/movies/{imdb_id}/similar")
def similar_movies(
    imdb_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=20),
):
    df = recommender.recommend_similar(imdb_id, offset, limit)
    return df.to_dict("records") if isinstance(df, pd.DataFrame) else []

# ===================== CREDITS =====================
@app.get("/movies/{imdb_id}/credits")
def movie_credits(imdb_id: str):
    return recommender.get_movie_credits(imdb_id)
