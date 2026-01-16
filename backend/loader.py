import os
import requests
import pandas as pd
import numpy as np
import pickle

# ===================== LOCAL DATA DIR =====================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ===================== HUGGING FACE FILE URLS =====================
FILES = {
    "movies.pkl": "https://huggingface.co/ScaryLeo/cinimatch-data/resolve/main/movies.pkl",
    "movie_vectors.pkl": "https://huggingface.co/ScaryLeo/cinimatch-data/resolve/main/movie_vectors.pkl",
    "rich_movies_dataset.csv": "https://huggingface.co/ScaryLeo/cinimatch-data/resolve/main/rich_movies_dataset.csv",
    "title_to_index.pkl": "https://huggingface.co/ScaryLeo/cinimatch-data/resolve/main/title_to_index.pkl",
}

# ===================== SIMPLE & RELIABLE DOWNLOADER =====================
def download_file(url, dest):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

# ===================== DOWNLOAD FILES IF MISSING =====================
for name, url in FILES.items():
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        print(f"⬇️ Downloading {name} from Hugging Face...")
        download_file(url, path)

print("✅ All data files ready")

# ===================== LOAD DATASET =====================
DATASET_PATH = os.path.join(DATA_DIR, "rich_movies_dataset.csv")

print("📥 Loading dataset...")
df = pd.read_csv(DATASET_PATH)

# ===================== CLEANING =====================
df.replace([np.inf, -np.inf], np.nan, inplace=True)

for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].fillna("")

for col in df.select_dtypes(include=["float", "int"]).columns:
    df[col] = df[col].fillna(0)

df = df.where(pd.notnull(df), None)

print("✅ Dataset cleaned & JSON-safe")

# ===================== SAFE PICKLE LOADING =====================
def safe_load_pickle(path, min_size_kb=10):
    if not os.path.exists(path):
        raise RuntimeError(f"Missing file: {path}")

    if os.path.getsize(path) < min_size_kb * 1024:
        raise RuntimeError(f"File corrupted or incomplete: {path}")

    with open(path, "rb") as f:
        return pickle.load(f)

movie_vectors = safe_load_pickle(os.path.join(DATA_DIR, "movie_vectors.pkl"))
movie_ids = safe_load_pickle(os.path.join(DATA_DIR, "movies.pkl"))
title_to_index = safe_load_pickle(os.path.join(DATA_DIR, "title_to_index.pkl"))

id_to_index = {mid: i for i, mid in enumerate(movie_ids)}

print("✅ Vectors & mappings loaded successfully")
