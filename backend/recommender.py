from functools import lru_cache
from typing import Optional, Sequence

import numpy as np
import pandas as pd
from scipy import sparse

from loader import load_catalog, normalize_text, split_set

DEFAULT_MIN_RATING = 6.5
DEFAULT_MIN_VOTES = 200
DEFAULT_YEAR_FROM = 1900

MOOD_MAP = {
    "dark": {"horror", "thriller", "mystery", "crime"},
    "light": {"comedy", "family", "animation"},
    "fast": {"action", "adventure", "sci-fi"},
    "emotional": {"drama", "romance"},
}


def catalog():
    return load_catalog()


def movies() -> pd.DataFrame:
    return catalog().df


def has_column(name: str) -> bool:
    return name in movies().columns


def safe_return(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.replace([np.inf, -np.inf], np.nan)
    public = frame.drop(
        columns=[col for col in frame.columns if col.startswith("_")],
        errors="ignore",
    )
    return public.where(pd.notnull(public), None)


def normalize(text) -> str:
    return normalize_text(text)


def enrich(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "rating_score" not in result.columns:
        result["rating_score"] = result["_rating_score"]
    if "votes_score" not in result.columns:
        result["votes_score"] = result["_votes_score"]
    if "popularity_score" not in result.columns:
        result["popularity_score"] = result["_popularity_score"]
    if "year_score" not in result.columns:
        result["year_score"] = result["_year_score"]
    return result


def quality_filter(
    frame: pd.DataFrame,
    min_rating: float = DEFAULT_MIN_RATING,
    min_votes: int = DEFAULT_MIN_VOTES,
    year_from: int = DEFAULT_YEAR_FROM,
    year_to: Optional[int] = None,
) -> pd.DataFrame:
    result = enrich(frame)
    if year_to is None:
        year_to = int(result["year_score"].max() or 2100)

    result = result[
        (result["rating_score"] >= min_rating)
        & (result["votes_score"] >= min_votes)
        & (result["year_score"] >= year_from)
        & (result["year_score"] <= year_to)
    ].copy()

    if "genres" in result.columns:
        result = result[
            ~result["genres"].str.lower().str.contains("adult", na=False, regex=False)
        ].copy()

    return result


def add_base_score(frame: pd.DataFrame, boost_col: str = "boost") -> pd.DataFrame:
    result = frame.copy()
    if result.empty:
        result["final_score"] = []
        return result

    max_year_value = result["year_score"].max()
    max_year = 2025 if pd.isna(max_year_value) else max(int(max_year_value), 2025)
    recency = ((result["year_score"] - 1980) / max(max_year - 1980, 1)).clip(0, 1)

    if boost_col not in result:
        result[boost_col] = 0.0

    result["final_score"] = (
        result["rating_score"] * 7
        + np.log1p(result["votes_score"]) * 4
        + np.log1p(result["popularity_score"]) * 6
        + recency * 5
        + result[boost_col]
    )
    return result


@lru_cache(maxsize=1)
def _trending_sorted() -> pd.DataFrame:
    result = quality_filter(movies(), min_rating=5.0, min_votes=20)
    result = add_base_score(result)
    return result.sort_values(
        ["popularity_score", "final_score", "votes_score"], ascending=False
    ).reset_index(drop=True)


def get_trending(offset: int = 0, limit: int = 10) -> pd.DataFrame:
    return safe_return(_trending_sorted().iloc[offset : offset + limit])


def search_movies(query, offset=0, limit=10):
    q = normalize(query)
    if not q:
        return safe_return(movies().iloc[0:0])

    frame = movies()
    titles = frame["_title_norm"]
    exact = titles.eq(q)
    starts = titles.str.startswith(q, na=False)
    contains = titles.str.contains(q, regex=False, na=False)

    result = enrich(frame[exact | starts | contains])
    result["search_rank"] = np.select([exact[result.index], starts[result.index]], [3, 2], default=1)
    result = add_base_score(result)
    result = result.sort_values(
        ["search_rank", "final_score", "popularity_score"], ascending=False
    )
    return safe_return(result.iloc[offset : offset + limit])


def get_movie_credits(imdb_id):
    frame = movies()
    movie = frame[frame["imdb_id"] == imdb_id]
    if movie.empty:
        return {"cast": [], "crew": []}

    row = movie.iloc[0]

    cast = []
    if has_column("_cast_set"):
        cast = [{"name": c.title()} for c in row.get("_cast_set", set())][:10]

    crew = []
    if has_column("directors") and row.get("directors"):
        crew.append({"name": row["directors"], "job": "Director"})

    return {"cast": cast, "crew": crew}


@lru_cache(maxsize=64)
def _genre_sorted(genre_key: str) -> pd.DataFrame:
    wanted = frozenset(genre_key.split("|"))
    result = quality_filter(movies(), min_rating=5.5, min_votes=50)
    result["genre_match"] = result["_genre_set"].apply(lambda g: len(wanted & g))
    result = result[result["genre_match"] > 0].copy()
    result["boost"] = result["genre_match"] * 8
    result = add_base_score(result)
    return result.sort_values(
        ["final_score", "genre_match", "rating_score", "votes_score"],
        ascending=False,
    ).reset_index(drop=True)


def recommend_by_genres(genres, offset: int = 0, limit: int = 10) -> pd.DataFrame:
    wanted = sorted({normalize(g) for g in genres or [] if normalize(g)})
    if not wanted:
        return get_trending(offset, limit)
    return safe_return(_genre_sorted("|".join(wanted)).iloc[offset : offset + limit])


def candidate_similarity_scores(imdb_id: str, candidate_indices: Sequence[int]) -> np.ndarray:
    data = catalog()
    if imdb_id not in data.id_to_index:
        return np.zeros(len(candidate_indices), dtype=float)

    if not candidate_indices:
        return np.array([], dtype=float)

    idx = data.id_to_index[imdb_id]
    if sparse.issparse(data.movie_vectors):
        scores = data.movie_vectors[list(candidate_indices)] @ data.movie_vectors[idx].T
        return np.asarray(scores.toarray()).ravel()
    return data.movie_vectors[list(candidate_indices)] @ data.movie_vectors[idx]


@lru_cache(maxsize=2048)
def top_similar_indices(imdb_id: str, limit: int = 500) -> tuple[int, ...]:
    data = catalog()
    if imdb_id not in data.id_to_index:
        return ()

    idx = data.id_to_index[imdb_id]
    if sparse.issparse(data.movie_vectors):
        scores = data.movie_vectors @ data.movie_vectors[idx].T
        scores = np.asarray(scores.toarray()).ravel()
    else:
        scores = data.movie_vectors @ data.movie_vectors[idx]
    scores[idx] = -1
    count = min(limit, len(scores))
    if count <= 0:
        return ()

    top = np.argpartition(scores, -count)[-count:]
    top = top[np.argsort(scores[top])[::-1]]
    return tuple(int(i) for i in top if scores[i] > 0)


def recommend_similar(imdb_id: str, offset: int = 0, limit: int = 8) -> pd.DataFrame:
    data = catalog()
    frame = data.df
    if imdb_id not in data.id_to_index:
        return get_trending(offset, limit)

    idx = data.id_to_index[imdb_id]
    anchor = frame.iloc[idx]
    anchor_genres = anchor.get("_genre_set", set())

    result = quality_filter(frame, min_rating=5.5, min_votes=30)
    result = result[result["imdb_id"] != imdb_id].copy()
    result["genre_match"] = result["_genre_set"].apply(lambda g: len(anchor_genres & g))
    result = result[result["genre_match"] > 0].copy()
    result["boost"] = result["genre_match"] * 10

    top_indices = set(top_similar_indices(imdb_id))
    if top_indices:
        result["semantic_match"] = result.index.isin(top_indices).astype(int)
        semantic_result = result[result["semantic_match"] > 0].copy()
        if len(semantic_result) >= offset + limit:
            result = semantic_result

    if has_column("collection"):
        anchor_collection = anchor.get("collection")
        if anchor_collection:
            result["boost"] += result["collection"].eq(anchor_collection).astype(int) * 18

    if has_column("_director_norm"):
        anchor_director = anchor.get("_director_norm", "")
        if anchor_director:
            result["boost"] += result["_director_norm"].eq(anchor_director).astype(int) * 8

    if has_column("_cast_set"):
        anchor_cast = anchor.get("_cast_set", set())
        if anchor_cast:
            result["boost"] += result["_cast_set"].apply(lambda c: len(anchor_cast & c)) * 4

    if top_indices:
        if "semantic_match" not in result:
            result["semantic_match"] = result.index.isin(top_indices).astype(int)
        result["boost"] += result["semantic_match"] * 12

    similarities = candidate_similarity_scores(imdb_id, result.index.tolist())
    if len(similarities):
        result["boost"] += similarities * 20

    result = add_base_score(result)
    result = result.sort_values(
        ["final_score", "genre_match", "rating_score", "votes_score"], ascending=False
    )
    return safe_return(result.iloc[offset : offset + limit])


def resolve_anchor(movie):
    key = normalize(movie)
    if not key:
        return None

    data = catalog()
    frame = data.df
    if key in data.title_to_index:
        return frame.iloc[data.title_to_index[key]]

    matches = frame[frame["_title_norm"].str.contains(key, regex=False, na=False)]
    if matches.empty:
        return None

    matches = enrich(matches)
    return matches.sort_values(["popularity_score", "votes_score"], ascending=False).iloc[0]


def _apply_anchor_boost(result: pd.DataFrame, anchor) -> pd.DataFrame:
    """Apply similarity-based score boosts from an anchor movie."""
    anchor_imdb = anchor.get("imdb_id")
    result = result[result["imdb_id"] != anchor_imdb].copy()

    if has_column("collection"):
        anchor_collection = anchor.get("collection")
        if anchor_collection:
            result["boost"] += result["collection"].eq(anchor_collection).astype(int) * 18

    if has_column("_director_norm"):
        anchor_director = anchor.get("_director_norm", "")
        if anchor_director:
            result["boost"] += result["_director_norm"].eq(anchor_director).astype(int) * 8

    if has_column("_cast_set"):
        anchor_cast = anchor.get("_cast_set", set())
        if anchor_cast:
            result["boost"] += result["_cast_set"].apply(lambda c: len(anchor_cast & c)) * 4

    top_indices = set(top_similar_indices(anchor_imdb))
    if top_indices:
        result["semantic_match"] = result.index.isin(top_indices).astype(int)
        result["boost"] += result["semantic_match"] * 10

    similarities = candidate_similarity_scores(anchor_imdb, result.index.tolist())
    if len(similarities):
        result["boost"] += similarities * 16

    return result


def _apply_genre_mood_boost(
    result: pd.DataFrame,
    anchor_genres: set,
    user_genres: set,
    mood_genres: set,
) -> pd.DataFrame:
    """Score and optionally narrow candidates by genre/mood alignment."""
    result = result.copy()
    result["anchor_match"] = result["_genre_set"].apply(lambda g: len(anchor_genres & g))
    result["user_match"] = result["_genre_set"].apply(lambda g: len(user_genres & g))
    result["mood_match"] = result["_genre_set"].apply(lambda g: len(mood_genres & g))

    desired = anchor_genres | user_genres | mood_genres
    if desired:
        focused = result[
            (result["anchor_match"] > 0)
            | (result["user_match"] > 0)
            | (result["mood_match"] > 0)
        ].copy()
        if not focused.empty:
            result = focused

    result["boost"] = (
        result["anchor_match"] * 10
        + result["user_match"] * 9
        + result["mood_match"] * 7
    )
    return result


def personal_recommend(
    movie=None,
    genres=None,
    rating=None,
    mood=None,
    yearFrom=None,
    yearTo=None,
    offset: int = 0,
    limit: int = 10,
) -> pd.DataFrame:
    frame = movies()
    min_rating = float(rating or DEFAULT_MIN_RATING)
    from_year = int(yearFrom or 2000)
    to_year = int(yearTo or frame["_year_score"].max() or 2100)
    if from_year > to_year:
        from_year, to_year = to_year, from_year

    result = quality_filter(
        frame,
        min_rating=max(0.0, min(min_rating, 10.0)),
        min_votes=100,
        year_from=max(DEFAULT_YEAR_FROM, from_year),
        year_to=to_year,
    )

    anchor = resolve_anchor(movie)
    anchor_genres = anchor.get("_genre_set", set()) if anchor is not None else set()
    user_genres = {normalize(g) for g in genres or [] if normalize(g)}
    mood_genres = MOOD_MAP.get(normalize(mood), set())

    result = _apply_genre_mood_boost(result, anchor_genres, user_genres, mood_genres)

    if anchor is not None:
        result = _apply_anchor_boost(result, anchor)

    result = add_base_score(result)
    result = result.sort_values(
        ["final_score", "anchor_match", "user_match", "mood_match", "rating_score", "votes_score"],
        ascending=False,
    )
    return safe_return(result.drop_duplicates("imdb_id").iloc[offset : offset + limit])


def get_metadata():
    frame = movies()
    genre_values = sorted(
        {
            genre.title()
            for genres in frame["_genre_set"]
            for genre in genres
            if genre and genre != "adult"
        }
    )
    years = frame["_year_score"]
    return {
        "genres": genre_values,
        "moods": [mood.title() for mood in MOOD_MAP],
        "yearMin": int(years[years > 0].min() or DEFAULT_YEAR_FROM),
        "yearMax": int(years.max() or 2100),
        "movieCount": int(len(frame)),
        "datasetSha256": catalog().dataset_sha256,
    }
