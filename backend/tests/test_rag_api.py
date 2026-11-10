import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes.documents import _build_question_cache_key
from app.main import app


client = TestClient(app)


def create_pdf_bytes() -> bytes:
    pdf_path = Path(__file__).resolve().parent / "sample.pdf"
    if pdf_path.exists():
        return pdf_path.read_bytes()

    content = (
        "%PDF-1.4\n"
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        "4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 18 Tf 50 50 Td (Hello University) Tj ET\nendstream\nendobj\n"
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        "xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000062 00000 n \n0000000123 00000 n \n0000000245 00000 n \n0000000334 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n420\n%%EOF"
    )
    pdf_path.write_bytes(content.encode("latin-1"))
    return content.encode("latin-1")


def test_upload_document_rejects_invalid_file_type():
    response = client.post(
        "/api/documents",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_userquestion_requires_question_field():
    response = client.post(
        "/api/userquestion",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_answer_requires_request_id():
    response = client.get("/api/answer")
    assert response.status_code == 422


def test_same_question_reuses_cached_request(monkeypatch):
    question = "What is the ICog AI research focus?"
    cache: dict[str, str] = {}
    cached_request_id = "cached-request-123"
    cache_key = _build_question_cache_key(question)
    cache[cache_key] = cached_request_id
    cache[f"rag:request:{cached_request_id}"] = json.dumps(
        {
            "question": question,
            "retrieved_context": [{"filename": "icog.pdf", "page_number": 1, "text": "ICog focuses on AI research."}],
            "source_references": [{"filename": "icog.pdf", "page_number": 1}],
        }
    )

    async def fake_get(key: str):
        return cache.get(key)

    async def fake_set(key: str, value: str, ex: int | None = None):
        cache[key] = value
        return True

    async def fake_search_document_chunks(*, query_vector, limit):
        raise AssertionError("Redis cache should short-circuit repeated questions before vector search runs.")

    monkeypatch.setattr("app.api.routes.documents.redis_client.get", fake_get)
    monkeypatch.setattr("app.api.routes.documents.redis_client.set", fake_set)
    monkeypatch.setattr("app.api.routes.documents.generate_question_embedding", lambda question: [0.1, 0.2, 0.3])
    monkeypatch.setattr("app.api.routes.documents.search_document_chunks", fake_search_document_chunks)

    response = client.post("/api/userquestion", json={"question": question})

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"] == cached_request_id
    assert body["cached"] is True


def test_search_document_chunks_hybrid_blends_dense_and_keyword_overlap(monkeypatch):
    from app.services.vector_service import search_document_chunks

    async def fake_query_points(**kwargs):
        return SimpleNamespace(
            points=[
                SimpleNamespace(
                    payload={
                        "document_id": "doc-2",
                        "filename": "astronomy.pdf",
                        "page_number": 3,
                        "chunk_index": 1,
                        "text": "This is unrelated astronomy research and stars.",
                    },
                    score=0.91,
                ),
                SimpleNamespace(
                    payload={
                        "document_id": "doc-1",
                        "filename": "icog.pdf",
                        "page_number": 1,
                        "chunk_index": 0,
                        "text": "ICog AI research focuses on advanced language models.",
                    },
                    score=0.87,
                ),
            ]
        )

    async def fake_ensure_collection():
        return None

    monkeypatch.setattr("app.services.vector_service.ensure_collection", fake_ensure_collection)
    monkeypatch.setattr("app.services.vector_service.qdrant_client.query_points", fake_query_points)

    results = asyncio.run(
        search_document_chunks(
            query_vector=[0.1, 0.2, 0.3],
            query_text="ICog AI research",
            limit=5,
        )
    )

    assert results[0]["document_id"] == "doc-1"
    assert results[0]["filename"] == "icog.pdf"
    assert "score" in results[0]
