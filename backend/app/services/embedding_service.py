from __future__ import annotations

from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)

    return _model
def generate_embeddings(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()

    vectors = model.encode(
        list(texts),
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    array = np.asarray(vectors, dtype=np.float32)

    if array.ndim == 1:
        array = array.reshape(1, -1)

    if array.shape[1] != settings.EMBEDDING_DIMENSION:
        raise ValueError(
            "Embedding dimension mismatch: expected "
            f"{settings.EMBEDDING_DIMENSION}, got {array.shape[1]}."
        )

    return array.tolist()


def generate_question_embedding(question: str) -> list[float]:
    embeddings = generate_embeddings([question])

    if not embeddings:
        raise ValueError("Question embedding generation failed.")

    return embeddings[0]