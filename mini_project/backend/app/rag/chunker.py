from typing import List, Dict


def chunk_text(
    pages: List[Dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> List[Dict]:
    """
    Split PDF pages into overlapping text chunks.

    Args:
        pages: Page-wise extracted text.
        chunk_size: Approximate maximum number of characters.
        chunk_overlap: Number of overlapping characters.

    Returns:
        List of chunks containing:
        - text
        - page_number
        - chunk_index
    """

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    chunk_index = 0

    for page in pages:
        page_number = page["page_number"]
        text = page["text"]

        if not text:
            continue

        start = 0
        text_length = len(text)

        while start < text_length:

            end = min(start + chunk_size, text_length)

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "page_number": page_number,
                        "text": chunk,
                    }
                )

                chunk_index += 1

            if end >= text_length:
                break

            start = end - chunk_overlap

    return chunks