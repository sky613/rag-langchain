from functools import lru_cache

from fastapi import HTTPException, status
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings


def ensure_openai_configured() -> None:
    # API Key 누락은 외부 호출 전에 명확한 서버 설정 오류로 처리한다.
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY is not configured in backend .env",
        )


@lru_cache
def get_vector_store() -> Chroma:
    ensure_openai_configured()
    embeddings = OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=embeddings,
        persist_directory=settings.chroma_dir,
    )


@lru_cache
def get_chat_model() -> ChatOpenAI:
    ensure_openai_configured()
    # temperature 0으로 RAG/Agent 벤치마크 결과의 변동을 줄인다.
    return ChatOpenAI(model=settings.chat_model, temperature=0, api_key=settings.openai_api_key)
