#!/usr/bin/env python3
import pickle
import numpy as np
from PIL import Image
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity

import insightface
from insightface.app import FaceAnalysis

MODEL_PKL = "./face_knn_arcface.pkl"          # din pickle
THRESHOLD = 0.55                             # justera vid behov

def load_image_bgr(p):
    img = Image.open(p).convert("RGB")
    return np.array(img)[:, :, ::-1]  # RGB->BGR

def main(img_path: str):
    # 1) Ladda modell
    with open(MODEL_PKL, "rb") as f:
        bundle = pickle.load(f)
    clf = bundle["model"]
    le  = bundle["label_encoder"]

    # 2) Initiera ArcFace
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=0)

    # 3) Hämta embedding
    img = load_image_bgr(img_path)
    faces = app.get(img)
    if len(faces) != 1:
        print(f"⏭️ {img_path}: {len(faces)} ansikten hittades")
        return

    emb = faces[0].embedding.astype(np.float32)

    # 4) Prediktion
    pred_id = clf.predict([emb])[0]
    probs   = clf.predict_proba([emb])[0]
    prob    = probs[pred_id]
    name    = le.inverse_transform([pred_id])[0]

    # Närmaste prototyp för enkel öppen-sets-koll
    neigh_id = clf.kneighbors([emb], n_neighbors=1, return_distance=False)[0][0]
    proto    = clf._fit_X[neigh_id]
    cos_sim  = cosine_similarity([emb], [proto])[0, 0]

    if cos_sim < THRESHOLD:
        name = "UNKNOWN"

    print(f"Bild: {img_path}")
    print(f"Prediktion: {name}  |  Prob: {prob:.3f}  |  CosSim: {cos_sim:.3f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Användning: python test_model.py /sökväg/till/bild.jpg")
        sys.exit(1)
    main(sys.argv[1])
