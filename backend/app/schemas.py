from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ChatMode = Literal["rag", "agent"]


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    chunk_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    # rag: 항상 검색 후 답변하는 결정적 2-Step / agent: 모델이 tool 사용 여부를 결정
    mode: ChatMode = "rag"


class Source(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: int | None = None
    chunk_index: int
    snippet: str


class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    answer: str
    mode: ChatMode
    # 모델에 실제로 제공된 context chunk 목록
    sources: list[Source]
    # 답변 본문에서 인용된 chunk ID 중 실제 제공된 chunk에 해당하는 것만 남긴다.
    cited_chunk_ids: list[str]
    tool_calls: list[str] = []
    usage: TokenUsage
    latency_ms: int
    estimated_cost_usd: float
