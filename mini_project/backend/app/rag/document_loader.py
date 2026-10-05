from pathlib import Path
from typing import List, Dict

import pymupdf as fitz


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract text from a PDF page by page.

    Returns:
        [
            {
                "page_number": 1,
                "text": "..."
            },
            ...
        ]
    """

    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_file.suffix.lower() != ".pdf":
        raise ValueError(f"Unsupported file type: {pdf_file.suffix}")

    pages = []

    document = fitz.open(pdf_path)

    try:
        for page_index, page in enumerate(document):
            text = page.get_text("text")

            if text:
                text = clean_extracted_text(text)

            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": text,
                }
            )
    finally:
        document.close()

    return pages


def clean_extracted_text(text: str) -> str:
    """
    Basic PDF text cleaning.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    lines = []

    for line in text.split("\n"):
        line = " ".join(line.split())

        if line:
            lines.append(line)

    # Join cleaned lines
    cleaned = "\n".join(lines)

    # Remove excessive blank lines
    while "\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n", "\n\n")

    return cleaned.strip()