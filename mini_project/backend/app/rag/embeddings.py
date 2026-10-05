"""
Embeddings module for RAG pipeline.
Generates vector embeddings for text chunks and search queries.
Uses sentence-transformers if available, with fastembed as a fallback.
"""

import numpy as np

_model = None
_backend = None


def get_embedding_model():
    """Lazily loads and returns the embedding model instance."""
    global _model, _backend

    if _model is not None:
        return _model

    # Try sentence-transformers (PyTorch based)
    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _backend = "sentence-transformers"
        return _model
    except Exception as torch_err:
        # Fall back to fastembed (ONNX runtime based, no PyTorch needed)
        try:
            from fastembed import TextEmbedding

            _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            _backend = "fastembed"
            return _model
        except Exception as fastembed_err:
            raise RuntimeError(
                f"Failed to load any embedding provider. "
                f"sentence-transformers error: {torch_err}; "
                f"fastembed error: {fastembed_err}"
            )


def generate_embedding(text: str) -> np.ndarray:
    """
    Generates a 2D normalized float32 numpy array embedding for input text.
    Shape returned: (1, vector_dimension) suitable for FAISS.
    """
    model = get_embedding_model()

    # Ensure input is a string
    if not isinstance(text, str):
        text = str(text)

    if _backend == "sentence-transformers":
        embeddings = model.encode([text], normalize_embeddings=True)
        return np.array(embeddings, dtype=np.float32)

    elif _backend == "fastembed":
        embeddings = list(model.embed([text]))
        vec = np.array(embeddings[0], dtype=np.float32)
        
        # Normalize L2 norm for cosine similarity / inner product
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return np.expand_dims(vec, axis=0)

    else:
        raise RuntimeError("No valid embedding backend is initialized.")


# Compatibility alias for scripts expecting plural 'generate_embeddings'
generate_embeddings = generate_embedding