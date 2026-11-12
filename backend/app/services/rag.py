import re
from time import perf_counter

from langchain_core.documents import Document as LCDocument
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable

from app.core.config import settings
from app.schemas import ChatMode, ChatResponse, Source, TokenUsage
from app.services.llm import get_chat_model, get_vector_store

NO_CONTEXT_ANSWER = "I couldn't find relevant information in the uploaded documents to answer this question."

SYSTEM_PROMPT = f"""You answer questions using ONLY the provided context chunks.
Rules:
- Every factual statement must be supported by the context.
- Cite supporting chunks inline with their exact chunk ID in square brackets, e.g. [abc-123:0].
- Only cite chunk IDs that appear in the context. Never invent sources.
- If the context does not contain the answer, reply exactly: "{NO_CONTEXT_ANSWER}"
- Answer in the same language as the question."""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "Context:\n{context}\n\nQuestion: {question}"),
    ]
)

CITATION_PATTERN = re.compile(r"\[([^\[\]\s]+:\d+)\]")


def get_retriever(k: int | None = None) -> BaseRetriever:
    return get_vector_store().as_retriever(search_kwargs={"k": k or settings.retrieval_k})


def format_context(docs: list[LCDocument]) -> str:
    blocks = []
    for doc in docs:
        page = doc.metadata.get("page")
        location = f", page {page}" if page else ""
        blocks.append(f"[{doc.metadata['chunk_id']}] ({doc.metadata['filename']}{location})\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)


def build_rag_chain(llm: BaseChatModel) -> Runnable:
    # 2-Step RAG의 생성 단계: Prompt -> ChatModel. 검색 단계와 분리해 각각 교체/테스트할 수 있다.
    return RAG_PROMPT | llm


def to_sources(docs: list[LCDocument]) -> list[Source]:
    return [
        Source(
            chunk_id=doc.metadata["chunk_id"],
            document_id=doc.metadata["document_id"],
            filename=doc.metadata["filename"],
            page=doc.metadata.get("page"),
            chunk_index=doc.metadata["chunk_index"],
            snippet=doc.page_content[:300],
        )
        for doc in docs
    ]


def extract_citations(answer: str, sources: list[Source]) -> list[str]:
    # 모델이 제공되지 않은 chunk ID를 만들어내도 응답 citation에는 포함되지 않게 한다.
    known = {source.chunk_id for source in sources}
    cited = [chunk_id for chunk_id in CITATION_PATTERN.findall(answer) if chunk_id in known]
    return list(dict.fromkeys(cited))


def sum_usage(messages: list[BaseMessage]) -> TokenUsage:
    usage = TokenUsage()
    for message in messages:
        metadata = getattr(message, "usage_metadata", None)
        if metadata:
            usage.input_tokens += metadata.get("input_tokens", 0)
            usage.output_tokens += metadata.get("output_tokens", 0)
            usage.total_tokens += metadata.get("total_tokens", 0)
    return usage


def estimate_cost(usage: TokenUsage) -> float:
    # shortcut: query embedding 비용은 제외(chat 대비 매우 작음). 정확한 과금이 필요하면 embedding token도 합산한다.
    cost = (
        usage.input_tokens * settings.input_cost_per_million
        + usage.output_tokens * settings.output_cost_per_million
    ) / 1_000_000
    return round(cost, 6)


def build_response(
    answer: str,
    mode: ChatMode,
    docs: list[LCDocument],
    messages: list[BaseMessage],
    started_at: float,
    tool_calls: list[str] | None = None,
) -> ChatResponse:
    sources = to_sources(docs)
    usage = sum_usage(messages)
    return ChatResponse(
        answer=answer,
        mode=mode,
        sources=sources,
        cited_chunk_ids=extract_citations(answer, sources),
        tool_calls=tool_calls or [],
        usage=usage,
        latency_ms=round((perf_counter() - started_at) * 1000),
        estimated_cost_usd=estimate_cost(usage),
    )


def answer_with_rag(
    question: str,
    retriever: BaseRetriever | None = None,
    llm: BaseChatModel | None = None,
) -> ChatResponse:
    # 결정적 2-Step RAG: 항상 검색(Step 1) 후 검색 결과만으로 답변 생성(Step 2).
    started_at = perf_counter()
    docs = (retriever or get_retriever()).invoke(question)

    if not docs:
        # 검색 결과가 없으면 모델을 호출하지 않아 근거 없는 답변과 비용을 모두 막는다.
        return build_response(NO_CONTEXT_ANSWER, "rag", [], [], started_at)

    message: AIMessage = build_rag_chain(llm or get_chat_model()).invoke(
        {"context": format_context(docs), "question": question}
    )
    return build_response(message.text, "rag", docs, [message], started_at)
