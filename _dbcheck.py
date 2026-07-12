import sqlite3, datetime
con = sqlite3.connect("app.db")
con.row_factory = sqlite3.Row
for table, col in [("otps", "expires_at"), ("otps", "created_at"),
                   ("refresh_tokens", "expires_at"), ("refresh_tokens", "created_at")]:
    rows = con.execute(f"SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL").fetchall()
    aware = 0
    for r in rows:
        v = r[col]
        if v and ("+" in v or v.endswith("Z")):
            aware += 1
    print(f"{table}.{col}: {len(rows)} rows, tz-aware(+Z): {aware}")
con.close()
