import os
from pathlib import Path
import numpy as np
import cv2
from tqdm import tqdm
import insightface
import pickle

# Initiera InsightFace med CPU (eller byt till CUDAExecutionProvider om du har GPU)
app = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0)

# Katalog med undermappar, en per person
dataset_dir = Path("/home/marqs/Bilder/pr0n/Faces")  # Ändra till din sökväg

# Lista som ska sparas till pickle
face_db = []

# Gå igenom varje person
for person_dir in tqdm(dataset_dir.iterdir(), desc="Läser personer"):
    if not person_dir.is_dir():
        continue
    person_name = person_dir.name
    for img_path in person_dir.glob("*.*"):
        if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        faces = app.get(img)
        if not faces:
            continue

        face = faces[0]  # Vi tar första ansiktet
        embedding = face.embedding.astype(np.float32)

        face_db.append({
            "name": person_name,
            "image_path": str(img_path),
            "embedding": embedding
        })

# Spara databasen
with open("face_database_arcface.pkl", "wb") as f:
    pickle.dump(face_db, f)

print(f"✅ Sparade {len(face_db)} ansikten till 'face_database_arcface.pkl'")
