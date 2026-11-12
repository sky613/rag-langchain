from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import Base, engine
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # MVP에서는 Alembic 대신 앱 시작 시 테이블을 자동 생성한다.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="rag-langchain API", lifespan=lifespan)

# 프론트엔드 개발 서버에서 백엔드 API를 호출할 수 있도록 CORS를 설정한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "chat_model": settings.chat_model, "embedding_model": settings.embedding_model}
