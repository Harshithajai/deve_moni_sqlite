# app/rag/metadata.py
from pathlib import Path
import re
import pymupdf as fitz

def extract_document_metadata(pdf_path: str) -> dict:
    pdf_file = Path(pdf_path)
    document = fitz.open(pdf_path)
    try:
        pdf_metadata = document.metadata or {}
    finally:
        document.close()

    # Fallback to filename if pdf_metadata.get("title") is empty or "Untitled"
    raw_title = pdf_metadata.get("title", "").strip()
    if not raw_title or raw_title.lower() == "untitled":
        title = pdf_file.stem.replace("_", " ").replace("-", " ")
    else:
        title = raw_title

    authors = pdf_metadata.get("author", "")
    year = extract_year(pdf_metadata, pdf_file.name)
    doi = extract_doi(pdf_metadata, pdf_file.name)

    return {
        "title": title.title(),
        "authors": authors.strip(),
        "year": year,
        "doi": doi,
        "source": "guideline" if "guideline" in str(pdf_file).lower() else "peer-reviewed-literature",
        "document_type": "evidence-based-guideline" if "guideline" in str(pdf_file).lower() else "research-paper",
        "file_name": pdf_file.name,
    }

def extract_year(metadata: dict, filename: str):
    metadata_text = " ".join(str(v) for v in metadata.values() if v)
    match = re.search(r"\b(19|20)\d{2}\b", metadata_text) or re.search(r"\b(19|20)\d{2}\b", filename)
    return int(match.group()) if match else None

def extract_doi(metadata: dict, filename: str):
    doi_pattern = r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)"
    metadata_text = " ".join(str(v) for v in metadata.values() if v)
    match = re.search(doi_pattern, metadata_text, re.I) or re.search(doi_pattern, filename, re.I)
    return match.group(1).rstrip(".,)") if match else None