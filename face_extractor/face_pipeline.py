#!/usr/bin/env python3
import os
import sys
import json
import pickle
import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import face_recognition
import cv2
from tqdm.auto import tqdm

from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import KNeighborsClassifier
# Vill du hellre köra SVM: from sklearn.svm import SVC

# ------------------ Defaultkonfig ------------------
DEFAULT_DATA_ROOT = "/home/marqs/Bilder/pr0n_faces"   # personmappar med ansikten
DEFAULT_WORKDIR   = "./.face_work"                    # här läggs checkpoints/embeddings
EMB_FILE          = "embeddings.pkl"                  # numpy array + labels i pickle
PROC_FILE         = "processed.jsonl"                 # en rad per bild (json)
MODEL_FILE        = "face_model.pkl"
MIN_WIDTH         = 150
MIN_HEIGHT        = 150
# ---------------------------------------------------

def load_processed(proc_path: Path) -> set:
    done = set()
    if proc_path.exists():
        with proc_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done.add(rec["path"])
                except Exception:
                    continue
    return done

def append_processed(proc_path: Path, img_path: str, ok: bool):
    with proc_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"path": img_path, "ok": ok}) + "\n")

def load_embeddings(emb_path: Path) -> Tuple[List[np.ndarray], List[str]]:
    if not emb_path.exists():
        return [], []
    with emb_path.open("rb") as f:
        data = pickle.load(f)
    return data["X"], data["y"]

def save_embeddings(emb_path: Path, X: List[np.ndarray], y: List[str]):
    with emb_path.open("wb") as f:
        pickle.dump({"X": X, "y": y}, f, protocol=pickle.HIGHEST_PROTOCOL)

def iter_images(root: Path):
    for person_dir in root.glob("*"):
        if person_dir.is_dir():
            label = person_dir.name
            for p in person_dir.glob("*.jpg"):
                yield str(p), label
            for p in person_dir.glob("*.png"):
                yield str(p), label
            for p in person_dir.glob("*.jpeg"):
                yield str(p), label
            for p in person_dir.glob("*.bmp"):
                yield str(p), label

def compute_embedding(path: str):
    img = face_recognition.load_image_file(path)
    h, w = img.shape[:2]
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return None
    locs = face_recognition.face_locations(img, model="hog")
    if len(locs) != 1:
        return None
    encs = face_recognition.face_encodings(img, known_face_locations=locs)
    return encs[0] if encs else None

def encode(args):
    data_root = Path(args.data_root)
    workdir   = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    emb_path  = workdir / EMB_FILE
    proc_path = workdir / PROC_FILE

    # Läs in redan sparade embeddings & processed
    X, y = load_embeddings(emb_path)
    processed = load_processed(proc_path)

    # Samla alla bilder
    all_images = list(iter_images(data_root))
    todo = [(p, label) for p, label in all_images if p not in processed]

    if not todo:
        print("✅ Inget att göra – alla bilder är redan processade.")
        return

    print(f"🔍 Att bearbeta: {len(todo)} bilder (skippar {len(processed)})")

    try:
        for path, label in tqdm(todo, unit="img"):
            emb = None
            try:
                emb = compute_embedding(path)
                if emb is not None:
                    X.append(emb)
                    y.append(label)
                    append_processed(proc_path, path, True)
                else:
                    append_processed(proc_path, path, False)
            except Exception as e:
                append_processed(proc_path, path, False)
                # logga till stderr
                print(f"❌ {path}: {e}", file=sys.stderr)

            # Periodisk flush
            if len(X) % args.flush_every == 0:
                save_embeddings(emb_path, X, y)

    except KeyboardInterrupt:
        print("\n⏹️ Avbrutet med Ctrl-C, sparar nuvarande state...")
    finally:
        save_embeddings(emb_path, X, y)
        print(f"💾 Sparade embeddings ({len(X)} st) till {emb_path}")

def train(args):
    workdir   = Path(args.workdir)
    emb_path  = workdir / EMB_FILE
    model_out = Path(args.model_out)

    X_list, y_list = load_embeddings(emb_path)
    if not X_list:
        print("❌ Inga embeddings funna. Kör encode först.")
        sys.exit(1)

    X = np.vstack(X_list)
    y = np.array(y_list)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # räkna klass-storlekar
    counts = {cls: np.sum(y == cls) for cls in np.unique(y)}
    min_count = min(counts.values())
    k = 1 if min_count < args.min_per_class else args.k

    clf = KNeighborsClassifier(n_neighbors=k, weights="distance", metric="euclidean")
    clf.fit(X, y_enc)

    with model_out.open("wb") as f:
        pickle.dump({"model": clf, "label_encoder": le}, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"✅ Sparade modell ({len(np.unique(y))} klasser, k={k}) till {model_out}")

def main():
    p = argparse.ArgumentParser(description="Face embedding & training pipeline with resume + progressbar")
    p.add_argument("--data-root", default=DEFAULT_DATA_ROOT)
    p.add_argument("--workdir",   default=DEFAULT_WORKDIR)
    p.add_argument("--model-out", default=MODEL_FILE)
    p.add_argument("--mode", choices=["encode", "train", "both"], default="both")
    p.add_argument("--flush-every", type=int, default=200, help="Spara embeddings var N:e lyckade bild")
    p.add_argument("-k", type=int, default=3, help="K för KNN")
    p.add_argument("--min-per-class", type=int, default=2, help="Under detta används k=1")
    args = p.parse_args()

    if args.mode in ("encode", "both"):
        encode(args)
    if args.mode in ("train", "both"):
        train(args)

if __name__ == "__main__":
    main()
