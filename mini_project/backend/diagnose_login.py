"""Run from backend/:  python diagnose_login.py you@example.com YourPassword"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

env_before = os.environ.get("DATABASE_URL")          # set in Windows/system env?
from app.database import DATABASE_URL, engine
from app.auth import verify_password
from sqlalchemy import text

print("\n1) System env DATABASE_URL set before .env loaded:", "YES -> " + env_before if env_before else "no")
print("2) URL the app is really using:", DATABASE_URL.replace(DATABASE_URL.split(":")[2].split("@")[0], "****") if "@" in DATABASE_URL else DATABASE_URL)

with engine.connect() as c:
    print("3) Connected to database:", c.execute(text("select current_database()")).scalar())
    n = c.execute(text("select count(*) from users")).scalar()
    print("4) Rows in users table:", n)
    if n:
        print("   Emails:", [r[0] for r in c.execute(text("select email from users order by id limit 8"))], "...")
    if len(sys.argv) == 3:
        email, pw = sys.argv[1].strip().lower(), sys.argv[2]
        row = c.execute(text("select password_hash, is_active from users where email=:e"), {"e": email}).first()
        if not row:
            print(f"5) Email '{email}' NOT FOUND in this database")
        else:
            print(f"5) Email found. is_active={row[1]}  password matches={verify_password(pw, row[0])}")
