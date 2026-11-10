from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.documents import router as document_router
from app.core.config import settings
from app.database.qdrant import qdrant_client
from app.database.redis import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.ping()
        print("Redis connected successfully!")
    except Exception as exc:  # pragma: no cover - startup diagnostics
        print(f"Redis unavailable during startup: {exc}")

    try:
        await qdrant_client.get_collections()
        print("Qdrant connected successfully!")
    except Exception as exc:  # pragma: no cover - startup diagnostics
        print(f"Qdrant unavailable during startup: {exc}")

    try:
        yield
    finally:
        try:
            await redis_client.aclose()
        except Exception:
            pass

        try:
            await qdrant_client.close()
        except Exception:
            pass

        print("Database connections closed!")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
