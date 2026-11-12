from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 모든 값은 환경변수 또는 backend/.env에서 덮어쓸 수 있다.
    openai_api_key: str = ""
    chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    # 비용 추정용 단가(USD / 1M tokens). 모델을 바꾸면 함께 갱신한다.
    input_cost_per_million: float = 0.40
    output_cost_per_million: float = 1.60

    database_url: str = "sqlite:///./data/rag.db"
    chroma_dir: str = "./data/chroma"
    chroma_collection: str = "documents"

    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_k: int = 4
    max_upload_mb: int = 20

    # Vite 개발 서버에서 백엔드 API를 호출할 수 있도록 허용한다.
    cors_origins: list[str] = ["http://localhost:5173"]

    # 이전 버전 .env의 키(GEMINI_* 등)가 남아 있어도 기동이 실패하지 않도록 무시한다.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
