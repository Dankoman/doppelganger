import sqlite3
from pathlib import Path

db_path = Path("data/ppic_scraper_state.db")
if not db_path.exists():
    print("DB does not exist")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name, failed_attempts FROM models")
    rows = cur.fetchall()
    print("Total models:", len(rows))
    for r in rows:
        if 'svenja' in r[0].lower() or 'fay' in r[0].lower():
            print(r)
