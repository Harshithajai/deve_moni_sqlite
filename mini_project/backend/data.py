
"""
Seed script: loads students + observations from observation_data_expanded.csv
into devcare.db, with ONE shared professional linked to all children.

Run from the backend/ directory:
    python seed_students.py
"""

import csv
import sys
from datetime import datetime

# So `from app...` imports work when running from backend/
sys.path.insert(0, ".")

from app.database import SessionLocal, engine, Base
from app.models import User, Child, Observation, child_professional
from app.auth import hash_password


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "observation_data_expanded.csv"

# Shared professional
PROFESSIONAL_EMAIL = "professional@devcare.local"
PROFESSIONAL_NAME = "Dr. Shared Professional"
PROFESSIONAL_PASSWORD = "ChangeMe123!"

# Shared parent
PARENT_EMAIL = "parent.bulk@devcare.local"
PARENT_NAME = "Bulk Import Parent"
PARENT_PASSWORD = "ChangeMe123!"


# ============================================================
# GET OR CREATE USER
# ============================================================

def get_or_create_user(db, email, name, role, password):
    """
    Find an existing user by email.
    If the user does not exist, create one.
    """

    user = db.query(User).filter(User.email == email).first()

    if user:
        return user

    user = User(
        full_name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# DATE PARSER
# ============================================================

def parse_dob(dob_str):
    """
    CSV stores date of birth as DD/MM/YYYY.
    Example:
        15/06/2020
    """

    return datetime.strptime(dob_str, "%d/%m/%Y").date()


# ============================================================
# MAIN
# ============================================================

def main():

    # Create tables if they do not already exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # CREATE / GET SHARED PROFESSIONAL
        # ----------------------------------------------------

        professional = get_or_create_user(
            db,
            PROFESSIONAL_EMAIL,
            PROFESSIONAL_NAME,
            "professional",
            PROFESSIONAL_PASSWORD,
        )

        # ----------------------------------------------------
        # CREATE / GET SHARED PARENT
        # ----------------------------------------------------

        parent = get_or_create_user(
            db,
            PARENT_EMAIL,
            PARENT_NAME,
            "parent",
            PARENT_PASSWORD,
        )

        # ----------------------------------------------------
        # CONFIDENCE SCORES
        # ----------------------------------------------------

        confidence_by_domain = {
            "Communication": 92,
            "Social Interaction": 86,
            "Play": 81,
            "Motor Skills": 88,
            "General Development": 76,
        }

        # Store children already processed
        children_by_name = {}

        # Count observations inserted
        obs_count = 0

        # ----------------------------------------------------
        # READ CSV
        # ----------------------------------------------------

        with open(
            CSV_PATH,
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                # ------------------------------------------------
                # GET STUDENT NAME
                # ------------------------------------------------

                name = row["student_name"].strip()

                # ------------------------------------------------
                # CREATE / GET CHILD
                # ------------------------------------------------

                if name not in children_by_name:

                    child = db.query(Child).filter(
                        Child.name == name,
                        Child.parent_id == parent.id
                    ).first()

                    if not child:

                        child = Child(
                            parent_id=parent.id,
                            name=name,
                            date_of_birth=parse_dob(row["dob"]),
                            age=int(row["age"]),
                        )

                        db.add(child)
                        db.commit()
                        db.refresh(child)

                    # ------------------------------------------------
                    # LINK CHILD TO SHARED PROFESSIONAL
                    # ------------------------------------------------

                    already_linked = db.execute(
                        child_professional.select().where(
                            (child_professional.c.child_id == child.id)
                            &
                            (
                                child_professional.c.professional_id
                                == professional.id
                            )
                        )
                    ).first()

                    if not already_linked:

                        db.execute(
                            child_professional.insert().values(
                                child_id=child.id,
                                professional_id=professional.id,
                            )
                        )

                        db.commit()

                    children_by_name[name] = child

                # Get the child object
                child = children_by_name[name]

                # ------------------------------------------------
                # PARSE OBSERVATION DATE
                # ------------------------------------------------

                obs_date = datetime.strptime(
                    row["observation_date"],
                    "%Y-%m-%d"
                )

                # ------------------------------------------------
                # CHECK FOR EXISTING OBSERVATION
                # ------------------------------------------------

                existing = db.query(Observation).filter(
                    Observation.child_id == child.id,
                    Observation.observation_date == obs_date,
                    Observation.domain == row["domain"],
                ).first()

                # Skip if already inserted
                if existing:
                    continue

                # ------------------------------------------------
                # GET CONFIDENCE SCORE
                # ------------------------------------------------

                confidence_score = confidence_by_domain.get(
                    row["domain"],
                    75
                )

                # ------------------------------------------------
                # CREATE OBSERVATION
                # ------------------------------------------------

                observation = Observation(
                    child_id=child.id,
                    observation_text=row["observation_text"],
                    domain=row["domain"],
                    skill="General observation",
                    behavior="Observed during monitoring",
                    observation_date=obs_date,
                    confidence_score=confidence_score,
                )

                db.add(observation)

                obs_count += 1

        # ----------------------------------------------------
        # SAVE ALL OBSERVATIONS
        # ----------------------------------------------------

        db.commit()

        # ----------------------------------------------------
        # OUTPUT RESULTS
        # ----------------------------------------------------

        prof_id = professional.id
        parent_id = parent.id

        print()
        print("=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print(f"Professional: {PROFESSIONAL_EMAIL} (id={prof_id})")
        print(f"Parent:       {PARENT_EMAIL} (id={parent_id})")
        print(f"Children created/linked: {len(children_by_name)}")
        print(f"Observations inserted:   {obs_count}")

        print("=" * 60)
        print()

    except Exception as e:

        # Roll back if anything goes wrong
        db.rollback()

        print()
        print("=" * 60)
        print("ERROR WHILE SEEDING DATA")
        print("=" * 60)
        print(str(e))
        print("=" * 60)
        print()

        raise

    finally:

        # Always close database connection
        db.close()


# ============================================================
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":
    main()

