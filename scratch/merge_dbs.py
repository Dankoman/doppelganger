import sqlite3
import os

target_db = 'data/ppic_scraper_state.db'
source_dbs = ['data/uncertain_scraper_state.db', 'data/scraper_state.db']

def merge_db(target, source):
    print(f"Merging {source} into {target}...")
    conn = sqlite3.connect(target)
    cur = conn.cursor()
    
    # Attach the source database
    cur.execute(f"ATTACH DATABASE '{source}' AS source")
    
    # Merge models
    cur.execute("INSERT OR IGNORE INTO models SELECT * FROM source.models")
    # Update if source has more progress (optional, but INSERT OR IGNORE is safer for now)
    
    # Merge galleries
    cur.execute("INSERT OR IGNORE INTO galleries SELECT * FROM source.galleries")
    
    # Merge images
    cur.execute("INSERT OR IGNORE INTO images SELECT * FROM source.images")
    
    conn.commit()
    cur.execute("DETACH DATABASE source")
    conn.close()

for src in source_dbs:
    if os.path.exists(src):
        try:
            merge_db(target_db, src)
        except Exception as e:
            print(f"Failed to merge {src}: {e}")

print("Merge complete.")
