from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader


def validate_pdf_bytes(file_bytes: bytes) -> bool:
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise ValueError("Uploaded file is empty.")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")

    return True


def extract_pdf_pages(file_path: Path) -> list[dict[str, Any]]:
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file was not found: {file_path}")

    file_bytes = file_path.read_bytes()
    validate_pdf_bytes(file_bytes)

    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:  
        raise ValueError("Failed to read the uploaded PDF file.") from exc

    if len(reader.pages) == 0:
        raise ValueError("The PDF is empty or contains no readable pages.")

    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned = " ".join(text.split())
        if cleaned:
            pages.append({"page_number": page_number, "text": cleaned})

    if not pages:
        raise ValueError("The PDF is unreadable or contains no extractable text.")

    return pages
