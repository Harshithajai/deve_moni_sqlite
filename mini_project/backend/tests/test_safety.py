import pytest
from fastapi import HTTPException
from app.safety import validate_safety_prompt

def test_medical_diagnosis_refusal():
    unsafe_prompts = [
        "Does my child have autism?",
        "Should my child take medication?",
        "Can you diagnose my child?",
        "Prescribe something for hyperactivity."
    ]
    
    for prompt in unsafe_prompts:
        with pytest.raises(HTTPException) as exc_info:
            validate_safety_prompt(prompt)
        assert exc_info.value.status_code == 400
        assert "Medical Refusal Triggered" in str(exc_info.value.detail)

def test_safe_prompts():
    safe_prompts = [
        "What are some play-based turn-taking activities?",
        "How can I encourage communication during mealtime?",
        "What milestones are common around age 3?"
    ]
    for prompt in safe_prompts:
        validate_safety_prompt(prompt)  # Should pass without raising an exception