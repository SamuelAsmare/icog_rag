from __future__ import annotations
import hashlib
import json
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field
from app.core.config import settings
from app.database.redis import redis_client
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import (
    generate_embeddings,
    generate_question_embedding,
)
from app.services.gemini_service import GeminiService
from app.services.pdf_service import extract_pdf_pages, validate_pdf_bytes
from app.services.vector_service import (
    search_document_chunks,
    store_document_chunks,
)

router = APIRouter(prefix="/api")


class UserQuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


def _build_question_cache_key(question: str) -> str:
    normalized_question = " ".join(
        question.strip().lower().split()
    )

    digest = hashlib.sha256(
        normalized_question.encode("utf-8")
    ).hexdigest()

    return f"rag:question:{digest}"


@router.post("/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
) -> dict:

    if settings.ADMIN_API_KEY and not settings.ALLOW_UNAUTHENTICATED_UPLOADS:
        provided_key = (
            request.headers.get("X-Admin-Key")
            or request.headers.get("Authorization", "")
            .replace("Bearer ", "")
            .strip()
        )

        if not provided_key or provided_key != settings.ADMIN_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: admin API key required."
            )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A PDF file is required."
        )

    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes."
        )

    try:
        validate_pdf_bytes(content)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    document_id = __import__("uuid").uuid4().__str__()

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    storage_path = upload_dir / f"{document_id}.pdf"

    try:
        storage_path.write_bytes(content)

        pages = extract_pdf_pages(storage_path)

        chunks = chunk_pages(
            pages,
            document_id=document_id,
            filename=file.filename
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the PDF."
            )

        chunk_texts = [chunk["text"] for chunk in chunks]

        embeddings = generate_embeddings(chunk_texts)

        if len(embeddings) != len(chunks):
            raise HTTPException(
                status_code=500,
                detail="Embedding generation did not match chunk count."
            )

        indexed_chunks = [
            {
                **chunk,
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        stored_count = await store_document_chunks(indexed_chunks)

        if stored_count != len(indexed_chunks):
            raise HTTPException(
                status_code=500,
                detail="Qdrant did not confirm all vectors were stored."
            )

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

        raise HTTPException(
            status_code=500,
            detail=f"Document indexing failed: {exc}"
        ) from exc


@router.post("/userquestion")
async def submit_user_question(
    payload: UserQuestionRequest
) -> dict:

    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # STEP 1: Generate the question-based Redis key.
    cache_key = _build_question_cache_key(question)

    # STEP 2: Check whether the question already exists in Redis.
    try:
        cached_payload_raw = await redis_client.get(cache_key)

    except Exception:
        cached_payload_raw = None

    # STEP 3: CACHE HIT.
    if cached_payload_raw:

        try:
            cached_payload = json.loads(cached_payload_raw)

        except json.JSONDecodeError:
            cached_payload = None

        if cached_payload:
            print("[QUESTION CACHE HIT] Existing question found in Redis.")

            return {
                "request_id": cache_key,
                "message": "Relevant context retrieved successfully from cache",
                "sources": cached_payload.get("source_references", []),
                "cached": True,
            }

    # STEP 4: CACHE MISS.
    print("[QUESTION CACHE MISS] Question not found in Redis.")

    # Generate the question embedding.
    try:
        query_vector = generate_question_embedding(question)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {exc}"
        ) from exc

    # Retrieve relevant chunks from Qdrant.
    try:
        results = await search_document_chunks(
            query_vector=query_vector,
            limit=settings.TOP_K,
            query_text=question,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Qdrant retrieval error: {exc}"
        ) from exc

    # if not results:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="No relevant ICOG context was found for the question."
    #     )

    # Extract source references.
    source_refs = [
        {
            "filename": item["filename"],
            "page_number": item["page_number"],
        }
        for item in results
    ]

    # STEP 5: Store everything under ONE Redis key.
    payload_to_store = {
        "question": question,
        "retrieved_context": results,
        "source_references": source_refs,
        "answer": None,
    }

    try:
        await redis_client.set(
            cache_key,
            json.dumps(payload_to_store),
            ex=settings.RAG_REQUEST_TTL
        )

        print("[REDIS] Question and retrieved context cached successfully.")

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Redis storage failure: {exc}"
        ) from exc

    # STEP 6: Return the same cache key as the request identifier.
    return {
        "request_id": cache_key,
        "message": "Relevant context retrieved successfully",
        "sources": source_refs,
        "cached": False,
    }


@router.get("/answer")
async def generate_answer(
    request_id: str = Query(
        ...,
        description="Question cache key returned by the userquestion endpoint."
    )
) -> dict:

    # The request_id is now the actual Redis key.
    redis_key = request_id

    # STEP 1: Retrieve the question and context from Redis.
    try:
        raw_value = await redis_client.get(redis_key)

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Redis lookup failed: {exc}"
        ) from exc

    if not raw_value:
        raise HTTPException(
            status_code=404,
            detail="Request ID not found or has expired."
        )

    try:
        saved_request = json.loads(raw_value)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored request data is invalid."
        ) from exc

    question = saved_request.get("question")
    context = saved_request.get("retrieved_context")

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Request data is incomplete or expired."
        )

    # STEP 2: Check whether a Gemini answer already exists.
    cached_answer = saved_request.get("answer")

    if cached_answer:

        print("[ANSWER CACHE HIT] Existing answer found.")
        print("[ANSWER CACHE HIT] Skipping Gemini API call.")

        return {
            "request_id": request_id,
            "message": "Answer retrieved successfully from cache",
            "answer": cached_answer,
            "sources": saved_request.get("source_references", []),
            "cached": True,
        }

    print("[ANSWER CACHE MISS] No generated answer found.")
    print("[GEMINI] Sending question and retrieved context to Gemini...")

    # STEP 3: Generate the answer using Gemini.
    try:
        gemini_service = GeminiService()

        if context:
            # DOCUMENT-BASED ANSWER
            print("[RAG] Relevant document chunks found.")
            print("[GEMINI] Generating answer using document context...")

            answer = gemini_service.generate_answer(
                question,
                context
            )

        else:
            # GENERAL LLM ANSWER
            print("[GENERAL LLM] No relevant document chunks found.")
            print("[GEMINI] Generating answer using general knowledge...")

            answer = gemini_service.generate_general_answer(
                question
            )

        print("[GEMINI] Answer generated successfully.")

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini API error while generating the answer."
        ) from exc

    # STEP 4: Update the existing Redis value with the generated answer.
    saved_request["answer"] = answer

    try:
        await redis_client.set(
            redis_key,
            json.dumps(saved_request),
            ex=settings.RAG_REQUEST_TTL
        )

        print("[REDIS] Generated answer successfully saved in Redis.")

    except Exception as exc:
        print(f"[REDIS WARNING] Failed to cache generated answer: {exc}")

    # STEP 5: Return the generated answer.
    return {
        "request_id": request_id,
        "message": "Answer generated successfully",
        "answer": answer,
        "sources": saved_request.get("source_references", []),
        "cached": False,
    }