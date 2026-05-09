import math
import sys
from pathlib import Path

from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main  # noqa: E402


client = TestClient(main.app)


def assert_json_safe(value):
    if isinstance(value, dict):
        for item in value.values():
            assert_json_safe(item)
    elif isinstance(value, list):
        for item in value:
            assert_json_safe(item)
    elif isinstance(value, float):
        assert math.isfinite(value)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["movies"] > 0
    assert "x-process-time" in response.headers


def test_metadata_contract():
    response = client.get("/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["movieCount"] > 0
    assert data["yearMin"] <= data["yearMax"]
    assert "Action" in data["genres"]
    assert "Fast" in data["moods"]
    assert len(data["datasetSha256"]) == 64


def test_trending_returns_json_safe_movies():
    response = client.get("/trending", params={"limit": 5})
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) == 5
    assert all(movie["imdb_id"] for movie in movies)
    assert_json_safe(movies)


def test_search_is_literal_not_regex():
    response = client.get("/search", params={"q": "[[", "limit": 5})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_personal_recommend_applies_contract():
    response = client.post(
        "/personal-recommend",
        params={"limit": 5},
        json={
            "movie": "Interstellar",
            "genres": ["Sci-Fi", "Adventure"],
            "rating": 7,
            "mood": "Fast",
            "yearFrom": 2000,
            "yearTo": 2026,
        },
    )
    assert response.status_code == 200
    movies = response.json()
    assert 1 <= len(movies) <= 5
    assert all(movie["imdb_id"] != "tt0816692" for movie in movies)
    assert all(not any(key.startswith("_") for key in movie) for movie in movies)


def test_personal_recommend_accepts_reversed_year_range():
    response = client.post(
        "/personal-recommend",
        params={"limit": 3},
        json={"genres": ["Action"], "yearFrom": 2025, "yearTo": 2000},
    )
    assert response.status_code == 200
    assert len(response.json()) <= 3


def test_unknown_similar_movie_falls_back_to_trending():
    response = client.get("/movies/not-real/similar", params={"limit": 4})
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_invalid_payload_is_rejected():
    response = client.post(
        "/personal-recommend",
        json={"rating": 42, "genres": ["Action"]},
    )
    assert response.status_code == 422
