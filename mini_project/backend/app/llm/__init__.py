"""
LLM package for Phase 4.

This package provides:
- LLM provider abstraction
- Groq provider implementation
- Observation extraction prompts
- Observation analysis service
"""

from .base import LLMProvider
from .provider import GroqProvider, LLMProviderError
from .service import (
    ObservationAnalysisService,
    ObservationExtraction
)

__all__ = [
    "LLMProvider",
    "GroqProvider",
    "LLMProviderError",
    "ObservationAnalysisService",
    "ObservationExtraction",
]