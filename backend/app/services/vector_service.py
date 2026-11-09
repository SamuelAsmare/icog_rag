
from __future__ import annotations

from uuid import uuid4

from qdrant_client.http import models

from app.core.config import settings
from app.database.qdrant import qdrant_client


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
) -> list[dict]:

    await ensure_collection()

    top_k = limit or settings.TOP_K

    threshold = (
        similarity_threshold
        if similarity_threshold is not None
        else settings.SIMILARITY_THRESHOLD
    )

    results = await qdrant_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        score_threshold=threshold,
        with_payload=True,
    )

    return [
        {
            "document_id": result.payload.get("document_id"),
            "filename": result.payload.get("filename"),
            "page_number": result.payload.get("page_number"),
            "chunk_index": result.payload.get("chunk_index"),
            "text": result.payload.get("text"),
            "score": float(result.score),
        }
        for result in results.points
        if result.payload is not None
    ]
