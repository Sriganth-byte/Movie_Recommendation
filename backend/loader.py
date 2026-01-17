# loader.py
import pandas as pd
import numpy as np
import pickle

DATA_PATH = "data/rich_movies_dataset.csv"

print("📥 Loading dataset...")
df = pd.read_csv(DATA_PATH)

# ================= CRITICAL CLEANING =================
# FastAPI / JSON cannot handle NaN or inf values

df.replace([np.inf, -np.inf], np.nan, inplace=True)

# Fill text columns
for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].fillna("")

# Fill numeric columns
for col in df.select_dtypes(include=["float", "int"]).columns:
    df[col] = df[col].fillna(0)

# Ensure JSON-safe values
df = df.where(pd.notnull(df), None)

print("✅ Dataset cleaned & JSON-safe")

# ================= LOAD VECTORS =================

with open("data/movie_vectors.pkl", "rb") as f:
    movie_vectors = pickle.load(f)

with open("data/movie_ids.pkl", "rb") as f:
    movie_ids = pickle.load(f)

with open("data/title_to_index.pkl", "rb") as f:
    title_to_index = pickle.load(f)

id_to_index = {mid: i for i, mid in enumerate(movie_ids)}

print("✅ Vectors & mappings loaded")
