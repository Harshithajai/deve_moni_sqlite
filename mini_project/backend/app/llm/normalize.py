"""
Coerce whatever JSON the LLM returned into the exact shape that
AskAIResponse (app/schemas.py) expects.

Why: FastAPI validates the response strictly. A single "year": "n.d." or a
missing key from the LLM turns into a 500 error, which the frontend shows as
"Failed to process request". Your knowledge base makes this likely, because
most chunks have year=None / empty authors, and the LLM echoes that back.

Save as: backend/app/llm/normalize.py
"""

from typing import Any, Dict, List, Optional

DEFAULT_SAFETY_NOTE = (
    "This information is for developmental monitoring and caregiver support "
    "only. It is not a substitute for professional evaluation or medical advice."
)

_EMPTY_STRINGS = {"", "none", "null", "n/a", "na", "unknown", "n.d."}


def _to_int(value: Any) -> Optional[int]:
    """'2019' -> 2019, 'n.d.' / None / 'N/A' -> None."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_text(value: Any) -> str:
    """None -> '', list -> 'a, b', anything else -> str(value)."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _to_list(value: Any) -> List[str]:
    """None -> [], 'text' -> ['text'], list -> list of str."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v is not None]
    return [str(value)]


def normalize_response(data: Any) -> Dict[str, Any]:
    """Return a dict that always satisfies AskAIResponse."""
    if not isinstance(data, dict):
        data = {}

    sources = []
    for src in data.get("evidence_sources") or []:
        if not isinstance(src, dict):
            continue
        doi = _to_text(src.get("doi")).strip()
        sources.append(
            {
                "title": _to_text(src.get("title")),
                "authors": _to_text(src.get("authors")),
                "year": _to_int(src.get("year")),
                "doi": None if doi.lower() in _EMPTY_STRINGS else doi,
                "page_number": _to_int(src.get("page_number")),
                "relevant_passage": _to_text(src.get("relevant_passage")),
            }
        )

    return {
        "answer": _to_text(data.get("answer"))
        or "I couldn't put together a complete answer. Please try rephrasing your question.",
        "why_this_may_help": _to_text(data.get("why_this_may_help")),
        "suggested_activities": _to_list(data.get("suggested_activities")),
        "how_to_try_at_home": _to_list(data.get("how_to_try_at_home")),
        "what_to_observe": _to_list(data.get("what_to_observe")),
        "evidence_sources": sources,
        "safety_note": _to_text(data.get("safety_note")) or DEFAULT_SAFETY_NOTE,
        "is_insufficient_evidence": bool(data.get("is_insufficient_evidence", False)),
    }