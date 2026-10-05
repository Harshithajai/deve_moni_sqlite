from pathlib import Path
import json
import faiss
import numpy as np

from app.rag.document_loader import extract_text_from_pdf
from app.rag.chunker import chunk_text
from app.rag.metadata import extract_document_metadata
from app.rag.embeddings import generate_embeddings
from app.rag.vector_store import save_vector_store

KNOWLEDGE_BASE_DIR = Path("../knowledge_base")

def ingest_documents():
    pdf_files = list(KNOWLEDGE_BASE_DIR.rglob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in knowledge_base/")
        return

    all_chunks = []
    all_texts = []

    for pdf_path in pdf_files:
        print(f"Ingesting: {pdf_path.name}")
        pages = extract_text_from_pdf(str(pdf_path))
        chunks = chunk_text(pages)
        doc_meta = extract_document_metadata(str(pdf_path))

        for chunk in chunks:
            chunk_data = {
                "text": chunk["text"],
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk["page_number"],
                **doc_meta
            }
            all_chunks.append(chunk_data)
            all_texts.append(chunk["text"])

    print("Generating Embeddings...")
    embeddings = generate_embeddings(all_texts)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(np.asarray(embeddings, dtype="float32"))

    save_vector_store(index, all_chunks)
    print("Ingestion complete successfully!")

if __name__ == "__main__":
    ingest_documents()