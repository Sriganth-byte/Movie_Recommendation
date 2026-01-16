import os
import shutil
import pandas as pd
import numpy as np
import pickle
from huggingface_hub import hf_hub_download

# ===================== LOCAL DATA DIR =====================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

REPO_ID = "ScaryLeo/cinimatch-data"

# ===================== DOWNLOAD FILES (SAFE COPY) =====================
def ensure_file(filename):
    local_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(local_path):
        print(f"⬇️ Downloading {filename} from Hugging Face...")
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            repo_type="dataset",
        )
        # 🔴 CRITICAL FIX: copy instead of replace
        shutil.copyfile(downloaded_path, local_path)
    return local_path

# Required files
DATASET_PATH = ensure_file("rich_movies_dataset.csv")
MOVIE_VECTORS_PATH = ensure_file("movie_vectors.pkl")
MOVIES_PATH = ensure_file("movies.pkl")
TITLE_TO_INDEX_PATH = ensure_file("title_to_index.pkl")

print("✅ All data files ready")

# ===================== LOAD DATASET =====================
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

# ===================== LOAD PICKLES =====================
with open(MOVIE_VECTORS_PATH, "rb") as f:
    movie_vectors = pickle.load(f)

with open(MOVIES_PATH, "rb") as f:
    movie_ids = pickle.load(f)

with open(TITLE_TO_INDEX_PATH, "rb") as f:
    title_to_index = pickle.load(f)

id_to_index = {mid: i for i, mid in enumerate(movie_ids)}

print("✅ Vectors & mappings loaded successfully")
