"""
LLM Service Module.

Provides services for:
1. Phase 4: Observation extraction and rule-based fallback.
2. Phase 6: Safety-checked, RAG-grounded caregiver query processing.
3. RAG Knowledgebase querying helper for activity recommendations.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.llm.provider import GroqProvider, LLMProviderError
from app.llm.prompts import (
    PHASE4_EXTRACTION_SYSTEM_PROMPT,
    build_phase4_extraction_prompt,
    SYSTEM_PROMPT as PHASE6_SYSTEM_PROMPT,
    build_phase6_assistant_prompt,
)
from app.rag.retriever import retrieve
from app.llm.normalize import normalize_response


# ================================================================
# DIAGNOSTIC / MEDICAL SAFETY KEYWORDS
# ================================================================

DIAGNOSTIC_KEYWORDS = [
    "autism",
    "asd",
    "adhd",
    "diagnose",
    "diagnosis",
    "disorder",
    "disability",
    "syndrome",
    "medication",
    "prescribe",
]


# ================================================================
# PHASE 4: STRUCTURED MODELS & RULE-BASED FALLBACK
# ================================================================


class ObservationExtraction(BaseModel):
    """Strict structured representation of an observation."""

    model_config = ConfigDict(extra="forbid")

    domain: Optional[str] = None
    skill: Optional[str] = None
    behavior: Optional[str] = None
    context: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


def _rule_based_fallback(text: str) -> ObservationExtraction:
    """
    Rule-based fallback when LLM observation extraction fails.
    """

    normalized = text.lower()

    communication_words = (
        "talk",
        "talked",
        "speak",
        "spoke",
        "word",
        "words",
        "language",
        "say",
        "said",
        "communicate",
        "communication",
    )

    if any(word in normalized for word in communication_words):
        return ObservationExtraction(
            domain="Communication",
            skill="Expressive communication",
            behavior="Child uses spoken or communicative language",
            confidence=0.85,
        )

    social_words = (
        "turn",
        "turns",
        "share",
        "shared",
        "friend",
        "friends",
        "social",
        "smile",
        "smiled",
        "play with",
        "played with",
        "join",
        "joined",
        "caregiver",
    )

    if any(word in normalized for word in social_words):
        return ObservationExtraction(
            domain="Social Interaction",
            skill="Social engagement",
            behavior="Child participates in social interaction",
            confidence=0.80,
        )

    play_words = (
        "play",
        "played",
        "playing",
        "toy",
        "toys",
        "game",
        "ball",
        "blocks",
        "pretend",
    )

    if any(word in normalized for word in play_words):
        return ObservationExtraction(
            domain="Play",
            skill="Play participation",
            behavior="Child engages in play or exploratory activity",
            confidence=0.82,
        )

    motor_words = (
        "walk",
        "walked",
        "run",
        "ran",
        "jump",
        "jumped",
        "climb",
        "climbed",
        "kick",
        "kicked",
        "throw",
        "threw",
        "catch",
        "caught",
    )

    if any(word in normalized for word in motor_words):
        return ObservationExtraction(
            domain="Motor Skills",
            skill="Gross motor movement",
            behavior="Child uses movement or motor action",
            confidence=0.87,
        )

    return ObservationExtraction(
        domain="General Development",
        skill="General observation",
        behavior="Developmental activity was observed",
        confidence=0.60,
    )


class ObservationAnalysisService:
    """Phase 4 Observation Analysis Service."""

    def __init__(self) -> None:
        fallback_setting = os.getenv(
            "LLM_FALLBACK_RULE_BASED",
            "true",
        ).strip().lower()

        self.fallback_enabled = fallback_setting in {
            "1",
            "true",
            "yes",
            "on",
        }

    def analyze(
        self,
        observation_text: str,
    ) -> tuple[ObservationExtraction, bool, Optional[str]]:

        if not observation_text or not observation_text.strip():
            raise ValueError("Observation text cannot be empty.")

        cleaned_text = observation_text.strip()

        try:
            provider = GroqProvider()

            user_prompt = build_phase4_extraction_prompt(
                cleaned_text
            )

            raw_result = provider.generate_json(
                system_prompt=PHASE4_EXTRACTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            extraction = ObservationExtraction.model_validate(
                raw_result
            )

            return extraction, False, None

        except (
            LLMProviderError,
            ValidationError,
            ValueError,
        ) as exc:

            if not self.fallback_enabled:
                raise LLMProviderError(
                    f"AI observation analysis failed: {exc}"
                ) from exc

            fallback_result = _rule_based_fallback(
                cleaned_text
            )

            warning = (
                "AI analysis was unavailable. "
                "The rule-based fallback was used instead. "
                "Please review the extracted information before saving."
            )

            return fallback_result, True, warning


# ================================================================
# PHASE 6: EVIDENCE-GROUNDED AI CAREGIVER ASSISTANT SERVICE
# ================================================================


def handle_diagnostic_query() -> Dict[str, Any]:
    """
    Safety response for diagnostic and medical queries.
    """

    return {
        "answer": (
            "I cannot provide diagnostic evaluations or determine "
            "if a child has a condition such as Autism Spectrum "
            "Disorder or ADHD."
        ),
        "why_this_may_help": (
            "Developmental variations are complex and require "
            "comprehensive clinical observation by trained "
            "medical professionals."
        ),
        "suggested_activities": [],
        "how_to_try_at_home": [],
        "what_to_observe": [
            "Document specific developmental behaviors "
            "in the Observation module.",
            "Note frequency and context of specific skills "
            "or challenges.",
        ],
        "evidence_sources": [],
        "safety_note": (
            "This application is intended for developmental "
            "monitoring and caregiver support. It is not a "
            "diagnostic tool or a substitute for professional "
            "medical advice. Please consult a qualified "
            "pediatrician or specialist."
        ),
        "is_insufficient_evidence": False,
    }


def _is_diagnostic_query(question: str) -> bool:
    """
    Checks whether the user is asking for diagnosis or medical
    treatment information.
    """

    if not question:
        return False

    question_lower = question.lower()

    return any(
        re.search(
            rf"\b{re.escape(keyword)}\b",
            question_lower,
        )
        for keyword in DIAGNOSTIC_KEYWORDS
    )


def process_caregiver_query(
    question: str,
    child_observations: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Phase 6 AI Assistant RAG pipeline.
    """

    # ------------------------------------------------------------
    # 1. Validate question
    # ------------------------------------------------------------

    if not question or not question.strip():
        return {
            "answer": "Please enter a question.",
            "why_this_may_help": "",
            "suggested_activities": [],
            "how_to_try_at_home": [],
            "what_to_observe": [],
            "evidence_sources": [],
            "safety_note": (
                "This application is intended for developmental "
                "monitoring and caregiver support."
            ),
            "is_insufficient_evidence": True,
        }

    question = question.strip()

    # ------------------------------------------------------------
    # 2. Diagnostic Safety Check
    # ------------------------------------------------------------

    if _is_diagnostic_query(question):
        return handle_diagnostic_query()

    # ------------------------------------------------------------
    # 3. RAG Semantic Retrieval
    # ------------------------------------------------------------

    try:
        retrieved_chunks = retrieve(
            query=question,
            top_k=4,
        )

    except Exception as exc:
        print(f"[RAG ERROR] {exc}")

        return {
            "answer": (
                "I was unable to access the local knowledge "
                "base right now. Please try again."
            ),
            "why_this_may_help": "",
            "suggested_activities": [],
            "how_to_try_at_home": [],
            "what_to_observe": [],
            "evidence_sources": [],
            "safety_note": (
                "This application is intended for developmental "
                "monitoring and caregiver support. It is not a "
                "diagnostic tool."
            ),
            "is_insufficient_evidence": True,
        }

    # ------------------------------------------------------------
    # 4. Check retrieved evidence
    # ------------------------------------------------------------

    if not retrieved_chunks:
        return {
            "answer": (
                "Insufficient evidence was retrieved to provide "
                "a reliable evidence-grounded answer."
            ),
            "why_this_may_help": "",
            "suggested_activities": [],
            "how_to_try_at_home": [],
            "what_to_observe": [],
            "evidence_sources": [],
            "safety_note": (
                "This application is intended for developmental "
                "monitoring and caregiver support. It is not a "
                "diagnostic tool."
            ),
            "is_insufficient_evidence": True,
        }

    # ------------------------------------------------------------
    # 5. Build formatted RAG context
    # ------------------------------------------------------------

    context_str = "RETRIEVED RESEARCH DOCUMENTS:\n"

    for idx, chunk in enumerate(retrieved_chunks):

        # Support both:
        # {"metadata": {...}, "text": "..."}
        #
        # and:
        # {"title": "...", "authors": "...", "text": "..."}
        meta = chunk.get("metadata", chunk)

        context_str += (
            f"\n[Source {idx + 1}]\n"
            f"Title: {meta.get('title', '')}\n"
            f"Authors: {meta.get('authors', '')}\n"
            f"Year: {meta.get('year', '')}\n"
            f"DOI: {meta.get('doi', '')}\n"
            f"Page: {meta.get('page_number', '')}\n"
            f"Text: {chunk.get('text', '')}\n"
        )

    # ------------------------------------------------------------
    # 6. Add child observations
    # ------------------------------------------------------------

    obs_context = None

    if child_observations:
        obs_context = "\n".join(
            f"- {obs}"
            for obs in child_observations
            if obs
        )

    # ------------------------------------------------------------
    # 7. Build LLM prompt
    # ------------------------------------------------------------

    user_payload = build_phase6_assistant_prompt(
        question=question,
        context_chunks=context_str,
        child_observations=obs_context,
    )

    # ------------------------------------------------------------
    # 8. Generate AI response
    # ------------------------------------------------------------

    try:
        provider = GroqProvider()

        raw_response = provider.generate(
            system_prompt=PHASE6_SYSTEM_PROMPT,
            user_prompt=user_payload,
        )

    except Exception as exc:

        print(f"[LLM ERROR] {exc}")

        return {
            "answer": (
                "The AI Assistant could not generate a response "
                "right now. Please check your Groq API key, "
                "LLM model configuration, and backend logs."
            ),
            "why_this_may_help": "",
            "suggested_activities": [],
            "how_to_try_at_home": [],
            "what_to_observe": [],
            "evidence_sources": [],
            "safety_note": (
                "This application is intended for developmental "
                "monitoring and caregiver support. It is not a "
                "diagnostic tool."
            ),
            "is_insufficient_evidence": True,
        }

    # ------------------------------------------------------------
    # 9. Parse JSON response
    # ------------------------------------------------------------

    try:

        clean_json = raw_response.strip()

        # Remove Markdown JSON fences
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]

        elif clean_json.startswith("```"):
            clean_json = clean_json[3:]

        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]

        data = json.loads(
            clean_json.strip()
        )

    except Exception as exc:

        print(f"[JSON PARSE ERROR] {exc}")
        print(f"[RAW RESPONSE] {raw_response}")

        return {
            "answer": (
                "The AI generated a response, but it was not "
                "in the expected format. Please try the question again."
            ),
            "why_this_may_help": "",
            "suggested_activities": [],
            "how_to_try_at_home": [],
            "what_to_observe": [],
            "evidence_sources": [],
            "safety_note": (
                "This application is intended for developmental "
                "monitoring and caregiver support. It is not a "
                "diagnostic tool."
            ),
            "is_insufficient_evidence": True,
        }

    # ------------------------------------------------------------
    # 9b. Normalize LLM response structure for FastAPI validation
    # ------------------------------------------------------------

    data = normalize_response(data)

    # ------------------------------------------------------------
    # 10. Validate citations
    # ------------------------------------------------------------

    valid_sources = []

    retrieved_titles = []

    for chunk in retrieved_chunks:

        meta = chunk.get("metadata", chunk)

        title = meta.get("title", "")

        if title:
            retrieved_titles.append(
                str(title).lower().strip()
            )

    for src in data.get("evidence_sources", []):

        if not isinstance(src, dict):
            continue

        src_title = str(
            src.get("title", "")
        ).lower().strip()

        if not src_title:
            continue

        if any(
            src_title in title or title in src_title
            for title in retrieved_titles
            if title
        ):
            valid_sources.append(src)

    data["evidence_sources"] = valid_sources

    # ------------------------------------------------------------
    # 11. Add citation warning if required
    # ------------------------------------------------------------

    if (
        not valid_sources
        and not data.get("is_insufficient_evidence")
    ):

        data["answer"] = (
            str(data.get("answer", ""))
            + "\n\n"
            "(Note: General strategies were provided, but "
            "no exact matching research citations were verified "
            "in the local knowledge base.)"
        )

    return data


# ================================================================
# RAG HELPER FUNCTION FOR ACTIVITY RECOMMENDATIONS
# ================================================================


def query_rag_knowledgebase(
    query: str,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Retrieves evidence from the RAG vector store and builds
    an evidence-grounded response.

    Used by activity services and general RAG helpers.
    """

    # ------------------------------------------------------------
    # 1. Validate query
    # ------------------------------------------------------------

    if not query or not query.strip():
        return {
            "response": "Please provide a query.",
            "citations": [],
        }

    query = query.strip()

    # ------------------------------------------------------------
    # 2. Diagnostic Safety Check
    # ------------------------------------------------------------

    if _is_diagnostic_query(query):

        diag_resp = handle_diagnostic_query()

        return {
            "response": diag_resp["answer"],
            "citations": [],
        }

    # ------------------------------------------------------------
    # 3. Retrieve relevant chunks
    # ------------------------------------------------------------

    try:

        chunks = retrieve(
            query=query,
            top_k=top_k,
        )

    except Exception as exc:

        print(f"[RAG ERROR] {exc}")

        return {
            "response": (
                "I was unable to access the knowledge base "
                "right now."
            ),
            "citations": [],
        }

    # ------------------------------------------------------------
    # 4. Check evidence
    # ------------------------------------------------------------

    if not chunks:

        return {
            "response": (
                "Insufficient evidence was retrieved to provide "
                "a reliable answer."
            ),
            "citations": [],
        }

    # ------------------------------------------------------------
    # 5. Extract context
    # ------------------------------------------------------------

    context_str = "\n\n".join(
        chunk.get("text", "")
        for chunk in chunks
    )

    # ------------------------------------------------------------
    # 6. Create prompt
    # ------------------------------------------------------------

    system_prompt = (
        "You are an evidence-grounded developmental caregiver "
        "assistant. Use the provided context to answer the "
        "caregiver query clearly, safely, and empathetically. "
        "Do not diagnose medical conditions."
    )

    user_prompt = (
        f"Context Guidelines:\n"
        f"{context_str}\n\n"
        f"Caregiver Query: {query}"
    )

    # ------------------------------------------------------------
    # 7. Generate response
    # ------------------------------------------------------------

    try:

        provider = GroqProvider()

        response_text = provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    except Exception as exc:

        print(f"[LLM ERROR] {exc}")

        return {
            "response": (
                "The AI Assistant could not generate a response "
                "right now. Please check the LLM configuration."
            ),
            "citations": chunks,
        }

    # ------------------------------------------------------------
    # 8. Return response
    # ------------------------------------------------------------

    return {
        "response": response_text,
        "citations": chunks,
    }