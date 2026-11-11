from sentence_transformers import CrossEncoder
model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int,
) -> list[dict]:

    if not chunks:
        return []

    pairs = [
        (query, chunk["text"] or "")
        for chunk in chunks
    ]

    scores = model.predict(pairs)

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    reranked_chunks = sorted(
        chunks,
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return reranked_chunks[:top_k]