#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArcFace-pipeline med progressbar & checkpoints.

- Läser data_root/person/*.jpg|png|...
- Detekterar ansikten med InsightFace (SCRFD), beräknar embeddings (ArcFace)
- Upsamplar små bilder innan detektion (valbart)
- Fallback: om ingen detektion -> direkt embedding på 112x112 (valbart)
- Sparar embeddings + etiketter i embeddings.pkl
- Tränar KNN (cosine) och sparar modell i face_knn_arcface.pkl
- Checkpoints: processed.jsonl + embeddings.pkl så du kan avbryta/fortsätta

Exempel:
  python face_arc_pipeline.py --mode both --data-root /home/marqs/Bilder/pr0n/Faces
"""

import sys
import json
import pickle
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image
from tqdm.auto import tqdm
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import KNeighborsClassifier

from insightface.app import FaceAnalysis

# ------------------ Default ------------------
DEFAULT_DATA_ROOT   = "/home/marqs/Bilder/pr0n/Faces"
DEFAULT_WORKDIR     = "./arcface_work"
EMB_PKL             = "embeddings.pkl"
PROC_JSONL          = "processed.jsonl"
MODEL_PKL           = "face_knn_arcface.pkl"

MIN_WIDTH           = 40
MIN_HEIGHT          = 40
UPSAMPLE_TARGET_MIN = 180   # minsta sida efter upsampling-försök

K_DEFAULT           = 3
MIN_PER_CLASS_DEF   = 2
# ---------------------------------------------


# -------------- Hjälpfunktioner --------------
def init_app(providers: List[str]) -> FaceAnalysis:
    app = FaceAnalysis(name="buffalo_l", providers=providers)
    app.prepare(ctx_id=0)
    return app

def load_processed(proc_path: Path) -> set:
    done = set()
    if proc_path.exists():
        with proc_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done.add(rec["path"])
                except Exception:
                    pass
    return done

def append_processed(proc_path: Path, img_path: str, ok: bool) -> None:
    with proc_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"path": img_path, "ok": ok}) + "\n")

def load_embeddings(emb_path: Path) -> Tuple[List[np.ndarray], List[str]]:
    if not emb_path.exists():
        return [], []
    with emb_path.open("rb") as f:
        data = pickle.load(f)
    return data["X"], data["y"]

def save_embeddings(emb_path: Path, X: List[np.ndarray], y: List[str]) -> None:
    tmp = emb_path.with_suffix(emb_path.suffix + ".tmp")
    with tmp.open("wb") as f:
        pickle.dump({"X": X, "y": y}, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(emb_path)

def iter_images(root: Path):
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    for person_dir in root.iterdir():
        if not person_dir.is_dir():
            continue
        label = person_dir.name
        for p in person_dir.iterdir():
            if p.suffix.lower() in exts:
                yield str(p), label

def load_image_rgb(path: str) -> Optional[np.ndarray]:
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return None
    return np.array(img)  # RGB

def rgb_to_bgr(arr: np.ndarray) -> np.ndarray:
    return arr[:, :, ::-1]

def upsample_if_needed(img_rgb: np.ndarray) -> np.ndarray:
    h, w = img_rgb.shape[:2]
    m = min(h, w)
    if m >= UPSAMPLE_TARGET_MIN:
        return img_rgb
    scale = UPSAMPLE_TARGET_MIN / m
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    return np.array(Image.fromarray(img_rgb).resize((new_w, new_h), Image.BICUBIC))

def get_embedding_direct(rec_model, img_rgb: np.ndarray) -> Optional[np.ndarray]:
    """Direkt embedding (bypass detektor). Resize → 112x112."""
    if img_rgb is None:
        return None
    img_112 = Image.fromarray(img_rgb).resize((112, 112), Image.BICUBIC)
    bgr = rgb_to_bgr(np.array(img_112)).astype(np.uint8)
    emb = rec_model.get(bgr)
    if emb is None or emb.size == 0:
        return None
    return emb.astype(np.float32)


# ----------- Embedding-funktion -----------
def compute_embedding(app: FaceAnalysis,
                      rec_model,
                      img_path: str,
                      allow_fallback: bool,
                      allow_upsample: bool,
                      verbose: bool = False) -> tuple[Optional[np.ndarray], int, bool]:
    """
    Returnerar (embedding, antal ansikten, fallback användes) och loggar detaljer om verbose är True.
    """
    img_rgb = load_image_rgb(img_path)
    if img_rgb is None:
        if verbose:
            print(f"[VERBOSE] {img_path}: failed to load image")
        return None, 0, False

    h, w = img_rgb.shape[:2]
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        if verbose:
            print(f"[VERBOSE] {img_path}: image too small ({w}x{h})")
        if allow_fallback:
            if verbose:
                print(f"[VERBOSE] {img_path}: trying direct fallback for small image")
            emb = get_embedding_direct(rec_model, img_rgb)
            if emb is None and verbose:
                print(f"[VERBOSE] {img_path}: fallback produced no embedding")
            return (emb, 1 if emb is not None else 0, True)
        return None, 0, False

    img_bgr = rgb_to_bgr(img_rgb)
    faces = app.get(img_bgr)
    n_faces = len(faces)
    if verbose:
        print(f"[VERBOSE] {img_path}: detector found {n_faces} face(s) on original")

    if n_faces == 0 and allow_upsample:
        if verbose:
            print(f"[VERBOSE] {img_path}: trying upsample before second pass")
        img_up = upsample_if_needed(img_rgb)
        if img_up is not img_rgb:
            faces = app.get(rgb_to_bgr(img_up))
            n_faces = len(faces)
            if verbose:
                print(f"[VERBOSE] {img_path}: detector found {n_faces} face(s) after upsample")
        elif verbose:
            print(f"[VERBOSE] {img_path}: upsample skipped (image already large enough)")

    if n_faces == 0 and allow_fallback:
        if verbose:
            print(f"[VERBOSE] {img_path}: trying direct fallback after detection failure")
        emb = get_embedding_direct(rec_model, img_rgb)
        if emb is None and verbose:
            print(f"[VERBOSE] {img_path}: fallback produced no embedding")
        return (emb, 1 if emb is not None else 0, True)

    if n_faces != 1:
        if verbose:
            print(f"[VERBOSE] {img_path}: rejecting because {n_faces} faces were detected")
        return None, n_faces, False

    emb = faces[0].embedding
    if emb is None or emb.size == 0:
        if verbose:
            print(f"[VERBOSE] {img_path}: embedding empty despite detection")
        return None, n_faces, False

    if verbose:
        print(f"[VERBOSE] {img_path}: embedding computed successfully")
    return emb.astype(np.float32), n_faces, False


# ----------------- Pipeline -----------------
def encode(args) -> None:
    data_root = Path(args.data_root)
    workdir   = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    emb_path  = workdir / EMB_PKL
    proc_path = workdir / PROC_JSONL

    X, y = load_embeddings(emb_path)
    processed = load_processed(proc_path)

    all_imgs = list(iter_images(data_root))
    todo = [(p, lbl) for p, lbl in all_imgs if p not in processed]

    if not todo:
        print("✅ Inget att göra – allt är redan processat.")
        return

    print(f"🔍 Att processa: {len(todo)} bilder (skippar {len(processed)})")

    app = init_app(["CPUExecutionProvider"])
    rec_model = app.models["recognition"]

    try:
        for path, label in tqdm(todo, unit="img"):
            ok = False
            try:
                emb, n, fb = compute_embedding(
                    app,
                    rec_model,
                    path,
                    allow_fallback=args.allow_fallback,
                    allow_upsample=args.allow_upsample,
                    verbose=args.verbose
                )
                if args.verbose:
                    status = "OK" if emb is not None and n == 1 else "FAIL"
                    print(f"[VERBOSE] {path}: final status {status} (faces={n}, fallback={fb})")
                if emb is not None and n == 1:
                    X.append(emb)
                    y.append(label)
                    ok = True
            except Exception as e:
                print(f"❌ {path}: {e}", file=sys.stderr)

            append_processed(proc_path, path, ok)

            if ok and (len(X) % args.flush_every == 0):
                save_embeddings(emb_path, X, y)

    except KeyboardInterrupt:
        print("\n⏹️ Avbrutet. Sparar state...")

    finally:
        save_embeddings(emb_path, X, y)
        print(f"💾 Sparade embeddings ({len(X)}) till {emb_path}")


def train(args) -> None:
    workdir   = Path(args.workdir)
    emb_path  = workdir / EMB_PKL
    model_out = Path(args.model_out)

    X_list, y_list = load_embeddings(emb_path)
    if not X_list:
        print("❌ Inga embeddings – kör encode först.")
        sys.exit(1)

    X = np.vstack(X_list)
    y = np.array(y_list)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    counts = {cls: np.sum(y == cls) for cls in np.unique(y)}
    min_count = min(counts.values())
    k = 1 if min_count < args.min_per_class else args.k

    clf = KNeighborsClassifier(n_neighbors=k, weights="distance", metric="cosine")
    clf.fit(X, y_enc)

    with model_out.open("wb") as f:
        pickle.dump({"model": clf, "label_encoder": le}, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"✅ Modell sparad: {model_out} (k={k}, klasser={len(np.unique(y))})")


# ------------------ CLI ---------------------
def main():
    ap = argparse.ArgumentParser(description="ArcFace-pipeline (progressbar + checkpoints, fallback & upsampling)")
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="Rotmapp med personmappar")
    ap.add_argument("--workdir",   default=DEFAULT_WORKDIR,   help="Arbetsmapp/checkpoints")
    ap.add_argument("--model-out", default=MODEL_PKL,         help="Filnamn för sparad modell (.pkl)")
    ap.add_argument("--mode", choices=["encode", "train", "both"], default="both")
    ap.add_argument("--flush-every", type=int, default=200, help="Spara embeddings var N:e lyckade bild")
    ap.add_argument("-k", type=int, default=K_DEFAULT, help="k för KNN")
    ap.add_argument("--min-per-class", type=int, default=MIN_PER_CLASS_DEF,
                    help="Om minsta klass < detta -> k=1")

    ap.add_argument("--allow-fallback", action="store_true",
                    help="Tillåt direkt embedding utan detektor om inga ansikten hittas")
    ap.add_argument("--allow-upsample", action="store_true",
                    help="Upsampla små bilder innan ny detektionskörning")

    ap.add_argument("--verbose", action="store_true",
                    help="Logga detaljerad status för varje bild")

    args = ap.parse_args()

    if args.mode in ("encode", "both"):
        encode(args)
    if args.mode in ("train", "both"):
        train(args)

if __name__ == "__main__":
    main()
