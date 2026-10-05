"""
One-time migration: copy all data from the old SQLite file (devcare.db)
into the PostgreSQL database configured in backend/.env.

Run from the backend/ folder (with your venv active):

    python migrate_sqlite_to_postgres.py            # copy data (skips if target already has users)
    python migrate_sqlite_to_postgres.py --force    # wipe target tables first, then copy

It is safe to run: the SQLite file is only READ, never modified.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import MetaData, create_engine, func, select, text

from app.database import DATABASE_URL, Base, engine as pg_engine
import app.models  # noqa: F401  (registers all tables on Base.metadata)

SQLITE_PATH = Path(__file__).resolve().parent / "devcare.db"

# Parents before children, so foreign keys are always satisfied.
TABLE_ORDER = [
    "users",
    "children",
    "research_documents",
    "research_chunks",
    "activities",
    "observations",
    "child_professional",
    "parent_professional",
    "activity_logs",
    "feedback",
    "ai_interactions",
    "activity_feedback",
]


def main(force: bool = False) -> None:
    if DATABASE_URL.startswith("sqlite"):
        sys.exit("DATABASE_URL in backend/.env still points to SQLite. Change it to your PostgreSQL URL first.")
    if not SQLITE_PATH.exists():
        sys.exit(f"SQLite file not found: {SQLITE_PATH}")

    # Make sure all tables exist in PostgreSQL
    Base.metadata.create_all(bind=pg_engine)

    sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH.as_posix()}")
    src_meta = MetaData()
    src_meta.reflect(bind=sqlite_engine)
    dst_tables = Base.metadata.tables

    missing = [t for t in TABLE_ORDER if t not in dst_tables]
    if missing:
        sys.exit(f"Tables missing from models: {missing}")

    with pg_engine.begin() as dst, sqlite_engine.connect() as src:
        existing_users = dst.execute(select(func.count()).select_from(dst_tables["users"])).scalar()
        if existing_users and not force:
            sys.exit(
                f"PostgreSQL already has {existing_users} users. Nothing copied.\n"
                "Re-run with --force to wipe the target tables and copy again."
            )

        if force:
            print("Wiping target tables...")
            names = ", ".join(f'"{t}"' for t in TABLE_ORDER)
            dst.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))

        for name in TABLE_ORDER:
            if name not in src_meta.tables:
                print(f"  {name:22s} (not in SQLite, skipped)")
                continue

            src_table = src_meta.tables[name]
            dst_table = dst_tables[name]
            dst_cols = {c.name for c in dst_table.columns}

            rows = []
            for row in src.execute(select(src_table)).mappings():
                # copy only columns that exist in the PostgreSQL model
                rows.append({k: v for k, v in row.items() if k in dst_cols})

            if rows:
                dst.execute(dst_table.insert(), rows)
            print(f"  {name:22s} {len(rows):5d} rows copied")

        # Explicit ids were inserted, so move each sequence past the max id.
        # Without this, the next INSERT (e.g. a new registration) fails with duplicate-key.
        print("Resetting id sequences...")
        for name in TABLE_ORDER:
            table = dst_tables[name]
            if "id" in table.columns:
                dst.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM \"{name}\"), 1), "
                    f"(SELECT COUNT(*) > 0 FROM \"{name}\"))"
                ))

    print("\nDone. Verifying row counts (SQLite vs PostgreSQL):")
    ok = True
    with pg_engine.connect() as dst, sqlite_engine.connect() as src:
        for name in TABLE_ORDER:
            if name not in src_meta.tables:
                continue
            s = src.execute(select(func.count()).select_from(src_meta.tables[name])).scalar()
            d = dst.execute(select(func.count()).select_from(dst_tables[name])).scalar()
            flag = "OK" if s == d else "MISMATCH"
            ok &= s == d
            print(f"  {name:22s} sqlite={s:5d}  postgres={d:5d}  {flag}")
    print("\nAll good." if ok else "\nSome counts differ - check the output above.")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
