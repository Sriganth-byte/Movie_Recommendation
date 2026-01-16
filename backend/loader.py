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

def download_from_drive(file_id, dest):
    URL = "https://drive.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={"id": file_id}, stream=True)
    token = None
    for k, v in response.cookies.items():
        if k.startswith("download_warning"):
            token = v

    if token:
        response = session.get(
            URL, params={"id": file_id, "confirm": token}, stream=True
        )

    with open(dest, "wb") as f:
        for chunk in response.iter_content(32768):
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

# ===================== LOAD VECTORS =====================
with open(os.path.join(DATA_DIR, "movie_vectors.pkl"), "rb") as f:
    movie_vectors = pickle.load(f)

with open(os.path.join(DATA_DIR, "movies.pkl"), "rb") as f:
    movie_ids = pickle.load(f)

with open(os.path.join(DATA_DIR, "title_to_index.pkl"), "rb") as f:
    title_to_index = pickle.load(f)

id_to_index = {mid: i for i, mid in enumerate(movie_ids)}

print("✅ Vectors & mappings loaded")
