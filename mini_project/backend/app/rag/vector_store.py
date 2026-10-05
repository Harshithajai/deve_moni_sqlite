"""
Vector store module using FAISS.
Handles saving and searching stored vector embeddings.
"""

import os
import pickle
from pathlib import Path
from typing import Any, Dict, List
import faiss

from app.rag.embeddings import generate_embedding

# Build path relative to the backend root directory
BACKEND_DIR = Path(__file__).resolve().parents[2]
VECTOR_STORE_DIR = BACKEND_DIR / "knowledge_base" / "vector_store"

INDEX_FILE = VECTOR_STORE_DIR / "index.faiss"
DOCUMENTS_FILE = VECTOR_STORE_DIR / "documents.pkl"
METADATA_FILE = DOCUMENTS_FILE  # Alias for scripts expecting METADATA_FILE


def save_vector_store(index: faiss.Index, documents: List[Dict[str, Any]]) -> None:
    """
    Saves the FAISS index and corresponding document chunks to disk.
    """
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    # Save FAISS index
    faiss.write_index(index, str(INDEX_FILE))

    # Save documents and metadata
    with open(DOCUMENTS_FILE, "wb") as f:
        pickle.dump(documents, f)

    print(f"[VECTOR STORE] Successfully saved FAISS index and {len(documents)} documents to {VECTOR_STORE_DIR}")


def search_vector_store(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Generates embedding for query and searches the FAISS index.
    """
    if not INDEX_FILE.exists() or not DOCUMENTS_FILE.exists():
        print(f"[VECTOR STORE ERROR] Index or documents file not found at {VECTOR_STORE_DIR}")
        return []

    # Load FAISS index and documents
    index = faiss.read_index(str(INDEX_FILE))
    with open(DOCUMENTS_FILE, "rb") as f:
        documents = pickle.load(f)

    # Generate query embedding vector
    query_vector = generate_embedding(query)

    # Perform similarity search
    distances, indices = index.search(query_vector, top_k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(documents):
            results.append(documents[idx])

    return results