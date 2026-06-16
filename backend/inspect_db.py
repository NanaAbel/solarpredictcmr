"""Quick script to inspect SolarPredict SQLite schema."""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "solar_predict.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print(f"Database: {DB}\n")

tables = cur.execute(
    "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print(f"Tables ({len(tables)}):")
for name, sql in tables:
    print(f"\n--- {name} ---")
    print(sql or "(no schema)")
    cols = cur.execute(f"PRAGMA table_info({name})").fetchall()
    for col in cols:
        cid, cname, ctype, notnull, default, pk = col
        flags = []
        if pk:
            flags.append("PK")
        if notnull:
            flags.append("NOT NULL")
        print(f"  {cname}: {ctype} {' '.join(flags)}")
    fks = cur.execute(f"PRAGMA foreign_key_list({name})").fetchall()
    if fks:
        print("  Foreign keys:")
        for fk in fks:
            print(f"    {fk[3]} -> {fk[2]}.{fk[4]}")
    else:
        print("  Foreign keys: none")

    count = cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"  Rows: {count}")

conn.close()
