import openai
from fastapi import APIRouter, HTTPException, status

from app.schemas import ChatRequest, ChatResponse
from app.services.agent import answer_with_agent
from app.services.rag import answer_with_rag

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        if payload.mode == "agent":
            return answer_with_agent(payload.question)
        return answer_with_rag(payload.question)
    except openai.OpenAIError as exc:
        # 외부 모델 호출 실패는 서버 내부 오류와 구분해 502로 반환한다.
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"OpenAI request failed: {exc}") from exc
