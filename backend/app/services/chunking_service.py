# Its responsibility is to take extracted PDF page texts and divide them into smaller pieces called chunks.
# from __future__ import annotations
from typing import Any, Iterable

from app.core.config import settings


def chunk_pages(
    pages: Iterable[dict[str, Any]],
    document_id: str,
    filename: str,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    step = max(1, chunk_size - overlap)

    for page in pages:
        page_text = str(page.get("text", "")).strip()
        if not page_text:
            continue

        words = page_text.split()
        page_number = int(page.get("page_number", 1))

        for chunk_index, start in enumerate(range(0, len(words), step)):
            chunk_words = words[start : start + chunk_size]
            if not chunk_words:
                continue

            chunk_text = " ".join(chunk_words)
            chunks.append(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_index": len(chunks),
                    "text": chunk_text,
                }
            )
    return chunks
