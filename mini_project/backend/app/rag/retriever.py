"""
RAG Retriever Module.
Provides vector search capabilities over the local knowledge base.
"""

import logging
from typing import Any, Dict, List, Optional
from app.rag.vector_store import search_vector_store

logger = logging.getLogger(__name__)


def retrieve(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieves the top_k most relevant document chunks for a query.
    
    Args:
        query: User search query or question.
        top_k: Number of relevant context chunks to retrieve.

    Returns:
        List of matching document chunks with text and metadata.
    """
    if not query or not query.strip():
        return []

    try:
        results = search_vector_store(query=query.strip(), top_k=top_k)
        return results if results else []
    except Exception as exc:
        logger.error(f"[RETRIEVER ERROR] Failed to retrieve context: {exc}")
        return []