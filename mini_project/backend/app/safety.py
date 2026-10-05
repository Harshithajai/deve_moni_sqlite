import re
from fastapi import HTTPException, status

MEDICAL_REFUSAL_KEYWORDS = [
    r"\bdiagnos(e|is|tic)\b",
    r"\bmedicat(e|ion|ions)\b",
    r"\bprescr(ibe|iption)\b",
    r"\bdoes my child have autism\b",
    r"\bcure\b",
    r"\btherapy treatment plan\b"
]

REFUSAL_MESSAGE = (
    "This platform provides evidence-grounded developmental support and observation monitoring. "
    "It does not offer medical diagnoses, clinical assessments, or treatment recommendations. "
    "Please consult a qualified healthcare professional or developmental specialist for clinical advice."
)

def validate_safety_prompt(prompt: str) -> None:
    for pattern in MEDICAL_REFUSAL_KEYWORDS:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Medical Refusal Triggered", "message": REFUSAL_MESSAGE}
            )