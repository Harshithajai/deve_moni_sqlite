"""Import the October 2026 school records into the configured Render database.

Run from the backend directory after setting RENDER_DATABASE_URL to the
database's External Database URL. The default is a dry run; pass --apply to
write records. The source SQLite database is read only.
"""
import argparse
import os
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, Table, and_, create_engine, func, select
from sqlalchemy.engine import Engine

BACKEND_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BACKEND_DIR / "devcare.db"
START_DATE = date(2026, 10, 5)
END_DATE = date(2026, 10, 17)
EXPECTED_DAYS = {
    date(2026, 10, day)
    for day in (5, 6, 7, 8, 9, 12, 13, 14, 15, 16)
}


def normalize_name(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name)
    return "".join(char for char in plain if char.isalnum()).upper()


ALIASES = {
    "MKMDAARIF": "AARIF",
    "MDAARIF": "AARIF",
    "DJORDANSAM": "JORDANSAM",
    "JORDENSAM": "JORDANSAM",
    "RSAMUDRA": "SAMUDRA",
    "SSAMUDRA": "SAMUDRA",
    "SYADHESWARAN": "YADHESWARAN",
    "SYADESHWARAN": "YADHESWARAN",
    "MUHAMMADYUSUF": "YUSUF",
    "MDYUSUF": "YUSUF",
    "ADEVESWARAN": "DEVESHWARAN",
    "ADEVESHWAR": "DEVESHWARAN",
    "RHASHIKA": "HASIKA",
    "RHASIKA": "HASIKA",
    "STARINI": "TARINI",
    "RSTARINI": "TARINI",
}


def student_key(name: str) -> str:
    normalized = normalize_name(name)
    return ALIASES.get(normalized, normalized)


def as_day(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def identity(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["observation_text"],
        row["domain"],
        row["skill"],
        row["behavior"],
        row["context"],
        row["confidence_score"],
    )


def require_tables(engine: Engine) -> tuple[Table, Table, Table]:
    metadata = MetaData()
    metadata.reflect(bind=engine, only=("children", "observations"))
    missing = {"children", "observations"} - set(metadata.tables)
    if missing:
        raise RuntimeError(
            "The target database is missing required tables: "
            + ", ".join(sorted(missing))
            + ". Deploy the application schema before importing."
        )
    children = metadata.tables["children"]
    observations = metadata.tables["observations"]
    required_child_columns = {"id", "name"}
    required_observation_columns = {
        "child_id",
        "observation_text",
        "domain",
        "skill",
        "behavior",
        "context",
        "confidence_score",
        "observation_date",
    }
    if not required_child_columns.issubset(children.c.keys()):
        raise RuntimeError("The target children table has an incompatible schema.")
    if not required_observation_columns.issubset(observations.c.keys()):
        raise RuntimeError("The target observations table has an incompatible schema.")
    return metadata, children, observations


def load_source_records() -> dict[tuple[str, date], dict[str, Any]]:
    if not SQLITE_PATH.is_file():
        raise RuntimeError(f"SQLite source database was not found: {SQLITE_PATH}")
    source_engine = create_engine(f"sqlite:///{SQLITE_PATH.as_posix()}")
    try:
        _, children, observations = require_tables(source_engine)
        query = (
            select(
                children.c.name,
                observations.c.observation_text,
                observations.c.domain,
                observations.c.skill,
                observations.c.behavior,
                observations.c.context,
                observations.c.confidence_score,
                observations.c.observation_date,
            )
            .select_from(
                observations.join(children, observations.c.child_id == children.c.id)
            )
            .where(
                and_(
                    observations.c.domain == "Education",
                    observations.c.skill == "School daily record",
                    func.date(observations.c.observation_date) >= START_DATE.isoformat(),
                    func.date(observations.c.observation_date) < END_DATE.isoformat(),
                )
            )
        )
        grouped: dict[tuple[str, date], list[dict[str, Any]]] = defaultdict(list)
        with source_engine.connect() as connection:
            for source in connection.execute(query).mappings():
                record = dict(source)
                day = as_day(record["observation_date"])
                grouped[(student_key(record["name"]), day)].append(record)
        if not grouped:
            raise RuntimeError(
                "No October school records were found in the local SQLite database."
            )
        if {day for _, day in grouped} != EXPECTED_DAYS:
            raise RuntimeError(
                "The local data does not contain exactly the expected 10 school days."
            )
        expected_students = 18
        students = {key for key, _ in grouped}
        if len(students) != expected_students:
            raise RuntimeError(
                f"Expected records for {expected_students} students; found {len(students)}."
            )
        records: dict[tuple[str, date], dict[str, Any]] = {}
        for key, copies in grouped.items():
            first = copies[0]
            if any(identity(copy) != identity(first) for copy in copies[1:]):
                raise RuntimeError(
                    "The local database contains conflicting records for a "
                    "student and date; import stopped without changes."
                )
            records[key] = {
                "observation_text": first["observation_text"],
                "domain": first["domain"],
                "skill": first["skill"],
                "behavior": first["behavior"],
                "context": first["context"],
                "confidence_score": first["confidence_score"],
                "observation_date": datetime.combine(key[1], time.min),
            }
        if len(records) != expected_students * len(EXPECTED_DAYS):
            raise RuntimeError(
                "Expected one school record per student per school day; "
                "the local data is incomplete."
            )
        return records
    finally:
        source_engine.dispose()


def import_records(target_engine: Engine, apply_changes: bool) -> tuple[int, int, int]:
    records = load_source_records()
    _, children, observations = require_tables(target_engine)
    target_children: dict[str, list[int]] = defaultdict(list)
    existing: dict[tuple[int, date], list[dict[str, Any]]] = defaultdict(list)
    inserts = []
    skipped = 0
    with target_engine.begin() as connection:
        for child in connection.execute(select(children.c.id, children.c.name)):
            target_children[student_key(child.name)].append(child.id)

        source_students = {key for key, _ in records}
        missing = source_students - target_children.keys()
        if missing:
            raise RuntimeError(
                f"{len(missing)} student name(s) from the import were not found "
                "in the target database. No records were changed."
            )

        target_ids = [
            child_id
            for key in source_students
            for child_id in target_children[key]
        ]
        query = select(
            observations.c.child_id,
            observations.c.observation_text,
            observations.c.domain,
            observations.c.skill,
            observations.c.behavior,
            observations.c.context,
            observations.c.confidence_score,
            observations.c.observation_date,
        ).where(
            and_(
                observations.c.child_id.in_(target_ids),
                observations.c.domain == "Education",
                observations.c.skill == "School daily record",
                func.date(observations.c.observation_date) >= START_DATE.isoformat(),
                func.date(observations.c.observation_date) < END_DATE.isoformat(),
            )
        )
        for row in connection.execute(query).mappings():
            existing[(row["child_id"], as_day(row["observation_date"]))].append(
                dict(row)
            )

        for (key, day), source_record in records.items():
            for child_id in target_children[key]:
                current = existing.get((child_id, day), [])
                if current:
                    if len(current) == 1 and identity(current[0]) == identity(source_record):
                        skipped += 1
                        continue
                    raise RuntimeError(
                        "A different school record already exists for a target "
                        "student and date. No records were changed."
                    )
                inserts.append({"child_id": child_id, **source_record})

        if apply_changes and inserts:
            connection.execute(observations.insert(), inserts)
    profile_count = sum(len(target_children[key]) for key in source_students)
    return len(inserts), skipped, profile_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the planned records; without this flag, perform a dry run",
    )
    args = parser.parse_args()
    database_url = os.environ.get("RENDER_DATABASE_URL", "").strip()
    if not database_url:
        sys.exit(
            "Set RENDER_DATABASE_URL to the Render PostgreSQL External Database "
            "URL in this terminal. Do not put it in a source file or commit it."
        )
    if args.apply and not database_url.startswith(("postgres://", "postgresql://", "postgresql+")):
        sys.exit("--apply is allowed only for a PostgreSQL target database.")
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgres://"):]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgresql://"):]

    target_engine = create_engine(database_url, pool_pre_ping=True)
    try:
        inserted, skipped, profile_count = import_records(target_engine, args.apply)
    finally:
        target_engine.dispose()

    if args.apply:
        print(
            f"Import complete for {profile_count} matching student profiles: "
            f"{inserted} records added; {skipped} exact duplicates skipped."
        )
    else:
        print(
            f"Dry run complete for {profile_count} matching student profiles: "
            f"{inserted} records would be added; "
            f"{skipped} exact duplicates would be skipped. No changes were made."
        )


if __name__ == "__main__":
    main()
