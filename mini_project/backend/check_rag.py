"""
Sanity check script to verify FAISS vector store retrieval.
Run from backend directory: python check_rag.py
"""

import sys
from pathlib import Path

# Ensure backend root is in python path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.embeddings import generate_embedding
from app.rag.vector_store import search_vector_store

def main():
    print("1) Testing embedding generation...")
    try:
        sample_vec = generate_embedding("Turn taking activities during play")
        print(f"   Success! Vector shape: {sample_vec.shape}")
    except Exception as err:
        print(f"   FAILED to generate embedding: {err}")
        return

    print("\n2) Testing FAISS vector store search...")
    try:
        results = search_vector_store("turn taking", top_k=2)
        if results:
            print(f"   Success! Retrieved {len(results)} chunks from vector store.")
            print(f"   Sample chunk excerpt: {results[0].get('text', '')[:100]}...")
        else:
            print("   Warning: Vector store returned 0 results.")
    except Exception as err:
        print(f"   FAILED to search vector store: {err}")

if __name__ == "__main__":
    main()