
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    APP_NAME: str = "ICOG RAG API"
    DEBUG: bool = True

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "documents"
    QDRANT_API_KEY: str | None = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str | None = None

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # File uploads
    UPLOAD_DIR: str = str(BASE_DIR / "storage" / "uploads")
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024

    # Dense embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Document chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80

    # Retrieval
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.20

    # Hybrid search and reranking
    RETRIEVAL_CANDIDATES: int = 30
    RERANK_TOP_K: int = 5
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # Redis request expiration
    RAG_REQUEST_TTL: int = 600

    # Admin
    ADMIN_API_KEY: str | None = None
    ALLOW_UNAUTHENTICATED_UPLOADS: bool = True

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def frontend_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.FRONTEND_URL.split(",")
            if origin.strip()
        ]


settings = Settings()
