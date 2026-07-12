import jwt
from datetime import datetime, timedelta, timezone

exp = datetime.now(timezone.utc) + timedelta(minutes=30)
payload = {"sub": "4", "role": "user", "type": "access", "exp": exp}
SECRET = "change-me-in-production-please-use-a-long-random-string"
try:
    tok = jwt.encode(payload, SECRET, algorithm="HS256")
    print("encode OK:", tok[:20], "...")
except Exception as e:
    print("ENCODE ERROR:", type(e).__name__, e)

try:
    d = jwt.decode(tok, SECRET, algorithms=["HS256"])
    print("decode OK, exp type:", type(d["exp"]))
except Exception as e:
    print("DECODE ERROR:", type(e).__name__, e)

aware = datetime.now(timezone.utc)
naive = datetime.now(timezone.utc).replace(tzinfo=None)
print("aware:", aware)
print("naive:", naive)
for a, b, lbl in [(aware, naive, "aware<naive"), (naive, aware, "naive<aware")]:
    try:
        print(lbl, "->", a < b)
    except Exception as e:
        print("COMPARE ERROR (" + lbl + "):", type(e).__name__, e)
