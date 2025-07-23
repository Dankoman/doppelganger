#!/usr/bin/env python3
import pickle, sys
from collections import defaultdict

PAIRS_FILE   = "dupes.txt"
EMB_IN       = "arcface_work/embeddings.pkl"
EMB_OUT      = "arcface_work/embeddings_merged.pkl"

# ---- Läs paren -------------------------------------------------
pairs = []
with open(PAIRS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        a, b = [s.strip() for s in line.split("|", 1)]
        pairs.append((a, b))

# ---- Union-Find för att slå ihop grupper -----------------------
parent = {}
def find(x):
    parent.setdefault(x, x)
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra

for a, b in pairs:
    union(a, b)

# Grupper
groups = defaultdict(list)
for lbl in list(parent.keys()):
    groups[find(lbl)].append(lbl)

# Välj kanonisk etikett (längst sträng, ändra om du vill)
alias_map = {}
for root, members in groups.items():
    canon = max(members, key=len)
    for m in members:
        alias_map[m] = canon

print("Alias-map:")
for k, v in alias_map.items():
    if k != v:
        print(f"{k} -> {v}")

# ---- Patcha embeddings -----------------------------------------
with open(EMB_IN, "rb") as f:
    data = pickle.load(f)

X = data["X"]
y = [alias_map.get(lbl, lbl) for lbl in data["y"]]

with open(EMB_OUT, "wb") as f:
    pickle.dump({"X": X, "y": y}, f, protocol=pickle.HIGHEST_PROTOCOL)

print(f"\n✅ Sparat {EMB_OUT}. Byt ut originalet eller ange rätt sökväg vid träning.")
