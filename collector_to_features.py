import json, os
import numpy as np
from feature_extractor import extract_dna_features

RAW_PATH = "data/raw"
OUT_PATH = "data/features"
os.makedirs(OUT_PATH, exist_ok=True)

def process_user(user_id):
    with open(f"{RAW_PATH}/{user_id}_raw.json") as f:
        raw = json.load(f)

    feature_vectors = []

    for sample in raw["samples"]:
        vec = extract_dna_features(sample)
        if vec is not None:
            feature_vectors.append(vec)

    X = np.array(feature_vectors)

    np.save(f"{OUT_PATH}/{user_id}_features.npy", X)
    print(f"[✓] Extracted {X.shape[0]} samples × {X.shape[1]} features")

if __name__ == "__main__":
    process_user("geshika")
