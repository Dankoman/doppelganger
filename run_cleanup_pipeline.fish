#!/usr/bin/env fish
# Kör hela rensnings- och omträningsflödet för ArcFace-projektet.
# Redigera variablerna nedan vid behov eller exportera motsvarande miljövariabler
# innan körning (t.ex. `set -x DATA_ROOT "/path"`).

set -e

function init_var --argument var default
    if not set -q $var
        set -g $var $default
    end
end

set script_dir (dirname (status -f))
cd $script_dir

init_var PYTHON "python3"
init_var DATA_ROOT "/home/marqs/Bilder/pBook"
init_var WORKDIR "$script_dir/arcface_work-ppic"
init_var REMOVE_FILE "$script_dir/remove.txt"
init_var MERGE_FILE "$script_dir/merge.txt"
init_var PROCESSED_JSON "$WORKDIR/processed-ppic.jsonl"
init_var EMBEDDINGS_PKL "$WORKDIR/embeddings_ppic.pkl"
init_var MERGED_EMBEDDINGS "$WORKDIR/embeddings_ppic_merged.pkl"
init_var MODEL_OUT "$WORKDIR/face_knn_arcface_ppic.pkl"

echo "[1/5] Tar bort poster ur processed-jsonl..."
$PYTHON remove_processed.py --processed $PROCESSED_JSON --remove $REMOVE_FILE --merge $MERGE_FILE; or exit $status

echo "[2/5] Tar bort embeddings baserat på alias..."
$PYTHON remove.py --embeddings $EMBEDDINGS_PKL --remove $REMOVE_FILE --no-alias; or exit $status

echo "[3/5] Kodar om embeddings från bildmappen..."
$PYTHON face_arc_pipeline.py --mode encode --data-root $DATA_ROOT --workdir $WORKDIR --allow-upsample --verbose; or exit $status

echo "[4/5] Uppdaterar alias-merge..."
$PYTHON merge.py; or exit $status

echo "[5/5] Tränar om KNN-modellen..."
$PYTHON face_arc_pipeline.py --mode train --embeddings $MERGED_EMBEDDINGS --model-out $MODEL_OUT; or exit $status

echo "Klart!"

# Töm face_extractor-filerna efter körning
set fe_dir (realpath "$script_dir/../face_extractor")
echo "Tömmer $fe_dir/remove.txt och $fe_dir/merge?.csv..."
echo -n > "$fe_dir/remove.txt"
echo -n > "$fe_dir/merge\?.csv"
