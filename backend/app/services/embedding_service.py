
from __future__ import annotations

from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


# Global variable used to store the loaded Sentence Transformer model.
# Initially, it is None because the model has not been loaded yet.
#
# We use a global variable so that the model does not need to be
# loaded from disk every time we generate an embedding.
#
# Once loaded, the same model instance can be reused for subsequent
# document uploads and user questions.
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Load and return the Sentence Transformer embedding model.

    This function uses lazy loading:
    - If the model has not been loaded, load it.
    - If the model is already loaded, reuse the existing instance.

    The model name is obtained from the application settings
    (settings.EMBEDDING_MODEL).
    """
    global _model

    # Check whether the embedding model has already been loaded.
    if _model is None:

        # Load the configured Sentence Transformer model.
        # For example: all-MiniLM-L6-v2.
        #
        # The model converts text into numerical vectors
        # that represent the semantic meaning of the text.
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)

    # Return the loaded model for generating embeddings.
    return _model


def generate_embeddings(texts: Sequence[str]) -> list[list[float]]:
    """
    Convert multiple text strings into numerical embedding vectors.

    This function is used mainly when indexing uploaded documents.
    After extracting text and splitting it into chunks, each chunk
    is converted into a vector before being stored in Qdrant.

    Args:
        texts: A sequence of text strings (document chunks or other text).

    Returns:
        A list of embedding vectors.
        Each vector contains floating-point numbers representing
        the semantic meaning of its corresponding text.
    """

    # If the input contains no text, return an empty list.
    # This prevents unnecessary model execution.
    if not texts:
        return []

    # Get the embedding model.
    # If it was already loaded, reuse it instead of loading it again.
    model = get_embedding_model()

    # Convert the input texts into numerical embedding vectors.
    vectors = model.encode(
        list(texts),

        # Process texts in batches of 32.
        # This helps manage memory when embedding many document chunks.
        batch_size=32,

        # Return the generated vectors as NumPy arrays
        # instead of the default output format.
        convert_to_numpy=True,

        # Normalize each embedding vector to have a magnitude of 1.
        # This is useful for cosine similarity calculations when
        # comparing document embeddings with question embeddings.
        normalize_embeddings=True,

        # Do not display a progress bar during embedding generation.
        show_progress_bar=False,
    )

    # Ensure the embeddings are stored as NumPy arrays
    # using float32 (32-bit floating-point numbers).
    #
    # float32 is commonly used for vector storage because it
    # provides a good balance between precision and memory usage.
    array = np.asarray(vectors, dtype=np.float32)

    # Ensure the embeddings have two dimensions:
    # (number of texts, embedding dimension).
    #
    # For example, a single embedding might initially look like:
    # [0.1, 0.2, 0.3]
    #
    # This converts it into:
    # [[0.1, 0.2, 0.3]]
    #
    # This makes the output shape consistent when processing
    # either one text or multiple texts.
    if array.ndim == 1:
        array = array.reshape(1, -1)

    # Validate that the generated embedding dimension matches
    # the dimension configured for the Qdrant collection.
    #
    # For example:
    # If the model generates 384 numbers per vector,
    # settings.EMBEDDING_DIMENSION must also be 384.
    #
    # If they do not match, raise an error because Qdrant
    # expects vectors with a consistent dimension.
    if array.shape[1] != settings.EMBEDDING_DIMENSION:
        raise ValueError(
            "Embedding dimension mismatch: expected "
            f"{settings.EMBEDDING_DIMENSION}, got {array.shape[1]}."
        )

    # Convert the NumPy array into ordinary Python lists.
    #
    # This makes the embeddings easier to pass to other
    # application services, such as the Qdrant storage service.
    #
    # The returned structure looks like:
    # [
    #     [0.1, 0.2, 0.3, ...],  # Embedding for first text
    #     [0.4, 0.5, 0.6, ...],  # Embedding for second text
    # ]
    return array.tolist()


def generate_question_embedding(question: str) -> list[float]:
    """
    Generate an embedding for a single user question.

    This function is mainly used during the retrieval stage of RAG.

    When a user submits a question:
    1. The question is converted into an embedding.
    2. The embedding is sent to Qdrant.
    3. Qdrant searches for document chunks with similar embeddings.
    4. The most relevant chunks are retrieved and passed to the LLM.

    Args:
        question: The user's question as a string.

    Returns:
        A single embedding vector (list of floating-point numbers).
    """

    # Reuse generate_embeddings() to convert the question into a vector.
    #
    # We put the question inside a list because generate_embeddings()
    # accepts multiple texts, even though we only have one question.
    embeddings = generate_embeddings([question])

    # Check whether embedding generation returned an empty result.
    # If it did, raise an error because we cannot search Qdrant
    # without a valid question embedding.
    if not embeddings:
        raise ValueError("Question embedding generation failed.")

    # Return the first (and only) embedding vector.
    #
    # generate_embeddings() returns a list of vectors,
    # but this function only needs one vector for one question.
    return embeddings[0]
