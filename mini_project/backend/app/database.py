import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Connection URL comes from the environment only (no hardcoded credentials).
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. Please set it in the environment or .env file."
    )

# Hosts hand out postgres:// or postgresql:// URLs. Pin the driver to psycopg2
# (the one in requirements.txt) so newer SQLAlchemy versions don't look for psycopg v3.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len("postgresql://"):]

print("[DATABASE] DATABASE_URL loaded.")

# PostgreSQL does not require connect_args like SQLite does
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args, 
    pool_pre_ping=True
)
print("[DATABASE] Created engine")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def ensure_legacy_schema():
    """Apply lightweight compatibility updates for legacy PostgreSQL schemas."""
    try:
        # Skip migration check if using SQLite
        if DATABASE_URL.startswith("sqlite"):
            print("[DATABASE] SQLite mode detected; skipping legacy schema migration.")
            return

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        def column_exists(table_name: str, column_name: str) -> bool:
            return column_name in {column["name"] for column in inspector.get_columns(table_name)}

        with engine.begin() as connection:
            if "users" in tables:
                if not column_exists("users", "full_name"):
                    connection.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255) NULL"))
                if column_exists("users", "name") and column_exists("users", "full_name"):
                    connection.execute(text("UPDATE users SET full_name = name WHERE full_name IS NULL OR full_name = ''"))
                    connection.execute(text("ALTER TABLE users ALTER COLUMN name DROP NOT NULL"))
                if not column_exists("users", "role"):
                    connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'parent'"))
                if not column_exists("users", "is_active"):
                    connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"))
                if not column_exists("users", "updated_at"):
                    connection.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"))
                if not column_exists("users", "created_at"):
                    connection.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"))

            if "children" in tables:
                if not column_exists("children", "parent_id") and column_exists("children", "user_id"):
                    connection.execute(text("ALTER TABLE children ADD COLUMN parent_id INT NULL"))
                    connection.execute(text("UPDATE children SET parent_id = user_id WHERE parent_id IS NULL"))
                    connection.execute(text("ALTER TABLE children ALTER COLUMN user_id DROP NOT NULL"))
                if not column_exists("children", "updated_at"):
                    connection.execute(text("ALTER TABLE children ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"))
                if not column_exists("children", "created_at"):
                    connection.execute(text("ALTER TABLE children ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"))

            if "observations" in tables:
                if not column_exists("observations", "confidence_score") and column_exists("observations", "confidence"):
                    connection.execute(text("ALTER TABLE observations ADD COLUMN confidence_score INT NULL"))
                    connection.execute(text("UPDATE observations SET confidence_score = confidence WHERE confidence_score IS NULL"))
                    connection.execute(text("ALTER TABLE observations ALTER COLUMN confidence DROP NOT NULL"))
                if not column_exists("observations", "created_at"):
                    connection.execute(text("ALTER TABLE observations ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"))

        print("[DATABASE] Legacy schema compatibility check complete.")
    except SQLAlchemyError as exc:
        print(f"[DATABASE] Schema compatibility check failed: {exc}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_available():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("[DATABASE] Health check: OK")
        return True
    except SQLAlchemyError as e:
        print(f"[DATABASE] Health check failed: {e}")
        return False