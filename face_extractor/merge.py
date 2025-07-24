#!/usr/bin/env python3
"""
Slår ihop alias enligt dupes.txt.
--dry-run : visa grupper och beräkna hur många etiketter ändras.
--apply   : skriv ny embeddings_merged.pkl (ändrar inget annat).
"""
import pickle, argparse
from collections import defaultdict

PAIRS = "dupes.txt"
EMB_IN  = "arcface_work/embeddings.pkl"
EMB_OUT = "arcface_work/embeddings_merged.pkl"

def load_pairs(fp):
    pairs = []
    with open(fp, encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"): continue
            a,b=[s.strip() for s in line.split("|",1)]
            pairs.append((a,b))
    return pairs

def build_alias_map(pairs):
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x: parent[x]=find(parent[x])
        return parent[x]
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[rb]=ra
    for a,b in pairs: union(a,b)
    groups=defaultdict(list)
    for k in list(parent): groups[find(k)].append(k)
    alias={}
    for root,members in groups.items():
        canon=max(members,key=len)        # välj längsta som kanoniskt
        for m in members: alias[m]=canon
    return alias,groups

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply",   action="store_true")
    args=ap.parse_args()

    if not (args.dry_run or args.apply):
        ap.error("ange --dry-run eller --apply")

    pairs=load_pairs(PAIRS)
    alias_map, groups = build_alias_map(pairs)

    print("➜ Föreslagna grupper:")
    for canon, members in sorted(groups.items()):
        if len(members)>1:
            print("  ", canon, "<-", ", ".join(sorted(set(members)-{canon})))

    if args.dry_run:
        print("\n(DRY-RUN) Inga filer skrivna.")
        return

    # --- Apply ---
    with open(EMB_IN,"rb") as f: data=pickle.load(f)
    X=data["X"]; y=[alias_map.get(lbl,lbl) for lbl in data["y"]]
    with open(EMB_OUT,"wb") as f:
        pickle.dump({"X":X,"y":y},f,pickle.HIGHEST_PROTOCOL)
    print(f"\n✅ Sparat {EMB_OUT} (ersätter {len(alias_map)} etiketter).")

if __name__=="__main__":
    main()
