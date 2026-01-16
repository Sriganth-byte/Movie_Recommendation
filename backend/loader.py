import os
import requests
import pandas as pd
import numpy as np
import pickle

# ===================== LOCAL DATA DIR (FREE TIER SAFE) =====================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ===================== GOOGLE DRIVE FILE IDS =====================
FILES = {
    "movies.pkl": "1iTAdBS-yVG0Fv3VSzEXxKvEq39mWTDPE",
    "movie_vectors.pkl": "1GMFO1dg4du5Mus560ykUUgt7w2MBCDdN",
    "rich_movies_dataset.csv": "1-JOD63yiWJQPOUdGAlh9OXmg0YOgSI53",
    "title_to_index.pkl": "1h053sS_NwNIY6eYlHGQ2OWtTISzMUvE8",
}

# ===================== ROBUST GOOGLE DRIVE DOWNLOADER =====================
def download_from_drive(file_id, dest):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={"id": file_id}, stream=True)

    # Handle Google Drive virus scan confirmation
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value

    if token:
        response = session.get(
            URL,
            params={"id": file_id, "confirm": token},
            stream=True,
        )

    # 🔴 CRITICAL: Ensure Drive did NOT return HTML
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        raise RuntimeError(
            f"Google Drive returned HTML instead of file for {dest}. "
            "Make sure the file is shared as 'Anyone with the link → Viewer'."
        )

    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)

# ===================== DOWNLOAD FILES IF MISSING =====================
for name, file_id in FILES.items():
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        print(f"⬇️ Downloading {name} from Google Drive...")
        download_from_drive(file_id, path)

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
        raise RuntimeError(
            f"File too small or corrupted: {path} "
            "(likely Google Drive HTML response)"
        )

    with open(path, "rb") as f:
        return pickle.load(f)

movie_vectors = safe_load_pickle(os.path.join(DATA_DIR, "movie_vectors.pkl"))
movie_ids = safe_load_pickle(os.path.join(DATA_DIR, "movies.pkl"))
title_to_index = safe_load_pickle(os.path.join(DATA_DIR, "title_to_index.pkl"))

id_to_index = {mid: i for i, mid in enumerate(movie_ids)}

print("✅ Vectors & mappings loaded successfully")
