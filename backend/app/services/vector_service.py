
from __future__ import annotations

import re
from uuid import uuid4

from qdrant_client.http import models

from app.core.config import settings
from app.database.qdrant import qdrant_client
from app.services.reranking_service import rerank_chunks

async def ensure_collection() -> None:
    try:
        response = await qdrant_client.get_collections()
    except Exception as exc:
        raise RuntimeError(
            "Qdrant connection failed during collection validation."
        ) from exc

    collection_names = [
        collection.name for collection in response.collections
    ]

    if settings.QDRANT_COLLECTION in collection_names:
        return

    await qdrant_client.create_collection(
        collection_name=settings.QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=settings.EMBEDDING_DIMENSION,
            distance=models.Distance.COSINE,
        ),
    )
async def store_document_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0
    await ensure_collection()
    points = [
        models.PointStruct(
            id=str(uuid4()),
            vector=chunk["embedding"],
            payload={
                "document_id": chunk["document_id"],
                "filename": chunk["filename"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
            },
        )
        for chunk in chunks
    ]
    await qdrant_client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        wait=True,
        points=points,
    )
    return len(points)
async def search_document_chunks(
    query_vector: list[float],
    limit: int | None = None,
    similarity_threshold: float | None = None,
    query_text: str | None = None,
) -> list[dict]:

    # 1. Determine how many final chunks we want.
    top_k = limit if limit is not None else settings.TOP_K

    threshold = (
        similarity_threshold
        if similarity_threshold is not None
        else settings.SIMILARITY_THRESHOLD
    )

    if top_k <= 0:
        return []

    # 2. COSINE SIMILARITY: Retrieve semantically similar candidates.
    await ensure_collection()

    results = await qdrant_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k * 3,
        score_threshold=threshold,
        with_payload=True,
    )

    # Convert Qdrant results into ordinary Python dictionaries.
    hits = [
        {
            "document_id": result.payload.get("document_id"),
            "filename": result.payload.get("filename"),
            "page_number": result.payload.get("page_number"),
            "chunk_index": result.payload.get("chunk_index"),
            "text": result.payload.get("text"),
            "cosine_score": float(result.score),
        }
        for result in results.points
        if result.payload is not None
    ]

    # Without the original question, we cannot perform
    # keyword matching or CrossEncoder reranking.
    if not query_text or not hits:
        return hits[:top_k]

    # 3. KEYWORD BOOSTING: Reward chunks containing query keywords.
    keyword_tokens = {
        token
        for token in re.findall(r"\w+", query_text.lower())
        if len(token) > 2
    }

    for hit in hits:
        text_tokens = {
            token
            for token in re.findall(r"\w+", (hit["text"] or "").lower())
            if len(token) > 2
        }

        if keyword_tokens:
            overlap = len(keyword_tokens & text_tokens)
            keyword_score = overlap / len(keyword_tokens)
        else:
            keyword_score = 0.0

        # Combine cosine similarity and keyword matching.
        hit["keyword_score"] = keyword_score

        hit["combined_score"] = (
            hit["cosine_score"] * 0.75
            + keyword_score * 0.25
        )

    # Put stronger preliminary candidates first.
    hits.sort(
        key=lambda item: item["combined_score"],
        reverse=True,
    )
    hits = hits[:top_k * 2]
    # 4. CROSSENCODER RERANKING:
    # Evaluate the question and each candidate chunk together.
    hits = rerank_chunks(
        query=query_text,
        chunks=hits,
        top_k=top_k,
    )

    # 5. Return the final top-k chunks.
    return hits