import sqlite3
import os

dbs = ['ppic_scraper_state.db', 'uncertain_scraper_state.db', 'scraper_state.db']
data_dir = 'data'

for db_name in dbs:
    db_path = os.path.join(data_dir, db_name)
    if not os.path.exists(db_path):
        print(f"Skipping {db_name} (not found)")
        continue
    print(f"\n--- {db_name} ---")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")
        cur.execute(f"PRAGMA table_info({table_name})")
        columns = cur.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    conn.close()
