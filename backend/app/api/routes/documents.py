from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.database.redis import redis_client
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import generate_embeddings, generate_question_embedding
from app.services.gemini_service import GeminiService
from app.services.pdf_service import extract_pdf_pages, validate_pdf_bytes
from app.services.vector_service import search_document_chunks, store_document_chunks

router = APIRouter(prefix="/api")


class UserQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


@router.post("/documents")
async def upload_document(request: Request, file: UploadFile = File(...)) -> dict:
    if settings.ADMIN_API_KEY and not settings.ALLOW_UNAUTHENTICATED_UPLOADS:
        provided_key = request.headers.get("X-Admin-Key") or request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        if not provided_key or provided_key != settings.ADMIN_API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized: admin API key required.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="A PDF file is required.")

    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes.",
        )

    try:
        validate_pdf_bytes(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    document_id = str(uuid4())
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_path = upload_dir / f"{document_id}.pdf"
    try:
        storage_path.write_bytes(content)
        pages = extract_pdf_pages(storage_path)
        chunks = chunk_pages(pages, document_id=document_id, filename=file.filename)
        if not chunks:
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF.")
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(chunk_texts)
        if len(embeddings) != len(chunks):
            raise HTTPException(status_code=500, detail="Embedding generation did not match chunk count.")

        indexed_chunks = [
            {
                **chunk,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        stored_count = await store_document_chunks(indexed_chunks)
        if stored_count != len(indexed_chunks):
            raise HTTPException(status_code=500, detail="Qdrant did not confirm all vectors were stored.")

        return {
            "success": True,
            "message": "Document indexed successfully.",
            "document_id": document_id,
            "filename": file.filename,
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "storage_path": str(storage_path),
        }
    except HTTPException:
        raise
    except Exception as exc:
        if storage_path.exists():
            storage_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {exc}") from exc


@router.post("/userquestion")
async def submit_user_question(payload: UserQuestionRequest) -> dict:
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        query_vector = generate_question_embedding(question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {exc}") from exc

    try:
        results = await search_document_chunks(query_vector=query_vector, limit=settings.TOP_K)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Qdrant retrieval error: {exc}") from exc

    if not results:
        raise HTTPException(status_code=404, detail="No relevant university context was found for the question.")

    request_id = str(uuid4())
    source_refs = [
        {
            "filename": item["filename"],
            "page_number": item["page_number"],
        }
        for item in results
    ]

    redis_key = f"rag:request:{request_id}"
    payload_to_store = {
        "question": question,
        "retrieved_context": results,
        "source_references": source_refs,
    }

    try:
        await redis_client.set(redis_key, json.dumps(payload_to_store), ex=settings.RAG_REQUEST_TTL)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Redis storage failure: {exc}") from exc

    return {
        "request_id": request_id,
        "message": "Relevant context retrieved successfully",
        "sources": source_refs,
    }


@router.get("/answer")
async def generate_answer(request_id: str = Query(..., description="Unique request ID from the question endpoint.")) -> dict:
    redis_key = f"rag:request:{request_id}"

    try:
        raw_value = await redis_client.get(redis_key)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Redis lookup failed: {exc}") from exc

    if not raw_value:
        raise HTTPException(status_code=404, detail="Request ID not found or has expired.")

    try:
        saved_request = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Stored request data is invalid.") from exc

    question = saved_request.get("question")
    context = saved_request.get("retrieved_context")
    if not question or not context:
        raise HTTPException(status_code=404, detail="Request data is incomplete or expired.")

    try:
        gemini_service = GeminiService()
        answer = gemini_service.generate_answer(question, context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Gemini API error while generating the answer.") from exc

    try:
        await redis_client.delete(redis_key)
    except Exception:
        pass

    return {
        "request_id": request_id,
        "message": "Answer generated successfully",
        "answer": answer,
        "sources": saved_request.get("source_references", []),
    }
