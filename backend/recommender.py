import numpy as np
import pandas as pd
import re
from sklearn.metrics.pairwise import cosine_similarity
from loader import df, movie_vectors, id_to_index, title_to_index

# ============================================================
# INTERNAL HELPERS
# ============================================================

def safe_return(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.replace([np.inf, -np.inf], np.nan)
    return frame.where(pd.notnull(frame), None)


def normalize(text):
    return text.lower().strip() if isinstance(text, str) else ""


def split_set(text):
    return {
        x.strip().lower()
        for x in str(text).split(",")
        if x.strip()
    }


HAS_CAST = "cast" in df.columns
HAS_COLLECTION = "collection" in df.columns
HAS_DIRECTOR = "directors" in df.columns

# ============================================================
# BASIC LISTS
# ============================================================

def get_trending(offset=0, limit=10):
    return safe_return(
        df.sort_values("popularity", ascending=False)
          .iloc[offset:offset + limit]
    )


def search_movies(query, offset=0, limit=10):
    q = normalize(query)
    mask = df["title"].str.lower().str.contains(q, na=False)
    return safe_return(
        df[mask].sort_values("popularity", ascending=False)
          .iloc[offset:offset + limit]
    )

# ============================================================
# CREDITS
# ============================================================

def get_movie_credits(imdb_id):
    movie = df[df["imdb_id"] == imdb_id]
    if movie.empty:
        return {"cast": [], "crew": []}

    row = movie.iloc[0]

    cast = []
    if HAS_CAST:
        cast = [{"name": c.strip()} for c in split_set(row.get("cast"))][:10]

    crew = []
    if HAS_DIRECTOR and row.get("directors"):
        crew.append({"name": row["directors"], "job": "Director"})

    return {"cast": cast, "crew": crew}

# ============================================================
# GENRE RECOMMENDATION (RESTORED)
# ============================================================

def recommend_by_genres(genres, offset=0, limit=10):
    if not genres:
        return get_trending(offset, limit)

    genres = {g.lower() for g in genres}

    result = df.copy()
    result["rating"] = result["vote_average"].fillna(0)
    result["votes"] = result["vote_count"].fillna(0)
    result["popularity_score"] = result["popularity"].fillna(0)

    result = result[result["genres"].apply(
        lambda g: bool(genres & split_set(g))
    )]

    result["final_score"] = (
        result["rating"] * 6 +
        np.log1p(result["votes"]) * 4 +
        result["popularity_score"] * 3
    )

    result = result.sort_values(
        ["final_score", "rating", "votes"],
        ascending=False
    )

    return safe_return(result.iloc[offset:offset + limit])

# ============================================================
# SIMILAR MOVIES
# ============================================================

def recommend_similar(imdb_id, offset=0, limit=8):
    if imdb_id not in id_to_index:
        return safe_return(df.sample(limit))

    idx = id_to_index[imdb_id]
    anchor = df.iloc[idx]

    anchor_genres = split_set(anchor.get("genres"))
    anchor_cast = split_set(anchor.get("cast")) if HAS_CAST else set()
    anchor_director = normalize(anchor.get("directors")) if HAS_DIRECTOR else ""
    anchor_collection = anchor.get("collection") if HAS_COLLECTION else None

    result = df.copy()

    result["genre_match"] = result["genres"].apply(
        lambda g: len(anchor_genres & split_set(g))
    )
    result = result[result["genre_match"] > 0].copy()

    result["rating"] = result["vote_average"].fillna(0)
    result["votes"] = result["vote_count"].fillna(0)
    result["popularity_score"] = result["popularity"].fillna(0)
    result["boost"] = 0.0

    if anchor_collection:
        result["boost"] += result["collection"].eq(anchor_collection).astype(int) * 4

    if anchor_director:
        result["boost"] += (
            result["directors"].str.lower().eq(anchor_director).astype(int) * 2.5
        )

    if anchor_cast and HAS_CAST:
        result["boost"] += result["cast"].apply(
            lambda c: len(anchor_cast & split_set(c))
        ) * 2

    sim = cosine_similarity(
        movie_vectors[idx].reshape(1, -1),
        movie_vectors
    ).flatten()

    result["boost"] += sim[result.index] * 0.5
    result = result[result["imdb_id"] != imdb_id]

    current_year = int(result["year"].max())

    result["final_score"] = (
        result["rating"] * 6 +
        np.log1p(result["votes"]) * 4 +
        result["popularity_score"] * 3 +
        (result["year"] - current_year) * 3 +
        result["boost"]
    )

    result = result.sort_values("final_score", ascending=False)

    return safe_return(result.iloc[offset:offset + limit])

# ============================================================
# PERSONAL RECOMMENDATION (MAIN ENGINE)
# ============================================================

MOOD_MAP = {
    "Dark": {"horror", "thriller", "mystery"},
    "Light": {"comedy", "family"},
    "Fast": {"action", "adventure"},
    "Emotional": {"drama", "romance"},
}

def personal_recommend(
    movie=None,
    genres=None,
    rating=None,
    mood=None,
    yearFrom=None,
    yearTo=None,
    offset=0,
    limit=10,
):
    result = df.copy()

    result["rating"] = result["vote_average"].fillna(0)
    result["votes"] = result["vote_count"].fillna(0)
    result["popularity_score"] = result["popularity"].fillna(0)

    result = result[
        (result["rating"] >= 6.5) &
        (result["votes"] >= 2000) &
        (result["year"] > 1900)
    ].copy()

    anchor = None
    anchor_genres = set()
    anchor_cast = set()
    anchor_director = ""
    anchor_collection = None

    if movie and movie.lower() in title_to_index:
        anchor = df.iloc[title_to_index[movie.lower()]]
        anchor_genres = split_set(anchor.get("genres"))
        anchor_cast = split_set(anchor.get("cast")) if HAS_CAST else set()
        anchor_director = normalize(anchor.get("directors")) if HAS_DIRECTOR else ""
        anchor_collection = anchor.get("collection") if HAS_COLLECTION else None

    user_genres = {g.lower() for g in genres} if genres else set()
    mood_genres = MOOD_MAP.get(mood, set())

    def overlap(g, ref):
        return len(ref & split_set(g))

    result["anchor_match"] = result["genres"].apply(
        lambda g: overlap(g, anchor_genres)
    )
    result["user_match"] = result["genres"].apply(
        lambda g: overlap(g, user_genres)
    )

    primary = result[result["anchor_match"] > 0].copy()
    secondary = result[
        (result["anchor_match"] == 0) &
        (result["user_match"] > 0)
    ].copy()

    if primary.empty:
        primary = secondary.copy()
        secondary = result.copy()

    def apply_boost(frame):
        frame = frame.copy()
        frame["boost"] = 0.0

        if anchor is not None:
            if anchor_collection:
                frame["boost"] += frame["collection"].eq(anchor_collection).astype(int) * 4

            if anchor_director:
                frame["boost"] += (
                    frame["directors"].str.lower().eq(anchor_director).astype(int) * 2.5
                )

            if anchor_cast and HAS_CAST:
                frame["boost"] += frame["cast"].apply(
                    lambda c: overlap(c, anchor_cast)
                ) * 2

        return frame


    primary = apply_boost(primary)
    secondary = apply_boost(secondary)

    current_year = int(result["year"].max())

    def score(frame):
        frame["final_score"] = (
            frame["rating"] * 6 +
            np.log1p(frame["votes"]) * 4 +
            frame["popularity_score"] * 3 +
            (frame["year"] - current_year) * 3 +
            frame["boost"]
        )
        return frame.sort_values(
            ["final_score", "rating", "votes", "year"],
            ascending=False
        )

    merged = pd.concat([score(primary), score(secondary)]).drop_duplicates("imdb_id")

    return safe_return(merged.iloc[offset:offset + limit])
