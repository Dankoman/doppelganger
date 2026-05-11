import sqlite3
import os

target_db = 'data/ppic_scraper_state.db'
source_dbs = ['data/scraper_state.db'] # Already merged uncertain_scraper_state.db

def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [col[1] for col in cur.fetchall()]

def merge_db(target, source):
    print(f"Merging {source} into {target}...")
    t_conn = sqlite3.connect(target)
    s_conn = sqlite3.connect(source)
    
    tables = ['models', 'galleries', 'images']
    for table in tables:
        try:
            s_cols = get_columns(s_conn, table)
            t_cols = get_columns(t_conn, table)
            
            # Find common columns
            common_cols = [c for c in s_cols if c in t_cols]
            col_list = ", ".join(common_cols)
            
            # Prepare SQL
            sql = f"INSERT OR IGNORE INTO {table} ({col_list}) SELECT {col_list} FROM source.{table}"
            
            # We need to ATTACH to the TARGET connection
            cur = t_conn.cursor()
            cur.execute(f"ATTACH DATABASE '{source}' AS source")
            cur.execute(sql)
            t_conn.commit()
            cur.execute("DETACH DATABASE source")
            print(f"  Merged {table}")
        except Exception as e:
            print(f"  Failed to merge {table}: {e}")
            
    t_conn.close()
    s_conn.close()

for src in source_dbs:
    if os.path.exists(src):
        merge_db(target_db, src)

print("Merge complete.")
