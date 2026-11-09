from pathlib import Path

from fastapi.testclient import TestClient

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
