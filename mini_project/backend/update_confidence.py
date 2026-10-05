from app.database import SessionLocal
from app.models import Observation

db = SessionLocal()

confidence_by_domain = {
    "Communication": 92,
    "Social Interaction": 86,
    "Play": 81,
    "Motor Skills": 88,
    "General Development": 76,
}

observations = db.query(Observation).all()

for observation in observations:
    domain = observation.domain

    if domain in confidence_by_domain:
        observation.confidence_score = confidence_by_domain[domain]

db.commit()

print("\nConfidence scores updated successfully!\n")

for domain, confidence in confidence_by_domain.items():
    count = (
        db.query(Observation)
        .filter(Observation.domain == domain)
        .count()
    )

    print(f"{domain}: {confidence}% ({count} records)")

db.close()