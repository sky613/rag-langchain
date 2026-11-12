from collections.abc import Callable
from time import perf_counter

from langchain.agents import create_agent
from langchain.tools import BaseTool, tool
from langchain_core.documents import Document as LCDocument
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.retrievers import BaseRetriever
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas import ChatResponse
from app.services import ingestion
from app.services.llm import get_chat_model
from app.services.rag import NO_CONTEXT_ANSWER, SYSTEM_PROMPT, build_response, format_context, get_retriever

AGENT_PROMPT = f"""You are a document assistant with tools.
- Call `search_documents` when the question may be answered by the uploaded documents.
- Call `list_documents` when the user asks which documents are available.
- For greetings or questions unrelated to the documents, answer directly without tools.
When you answer from search results, follow these rules:
{SYSTEM_PROMPT}"""


def build_agent_tools(
    retriever: BaseRetriever,
    session_factory: Callable[[], Session] = SessionLocal,
) -> list[BaseTool]:
    @tool(response_format="content_and_artifact")
    def search_documents(query: str) -> tuple[str, list[LCDocument]]:
        """Search the uploaded documents for chunks relevant to the query."""
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant documents found.", []
        # artifact로 원본 Document를 함께 넘겨 응답 source를 모델 출력이 아닌 실제 검색 결과로 만든다.
        return format_context(docs), docs

    @tool
    def list_documents() -> str:
        """List the uploaded documents with their IDs and chunk counts."""
        with session_factory() as db:
            documents = ingestion.list_documents(db)
        if not documents:
            return "No documents uploaded."
        return "\n".join(f"- {doc.filename} (id={doc.id}, chunks={doc.chunk_count})" for doc in documents)

    return [search_documents, list_documents]


def answer_with_agent(
    question: str,
    retriever: BaseRetriever | None = None,
    llm: BaseChatModel | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
) -> ChatResponse:
    started_at = perf_counter()
    agent = create_agent(
        llm or get_chat_model(),
        tools=build_agent_tools(retriever or get_retriever(), session_factory),
        system_prompt=AGENT_PROMPT,
    )
    messages = agent.invoke({"messages": [{"role": "user", "content": question}]})["messages"]

    tool_calls = [call["name"] for message in messages if isinstance(message, AIMessage) for call in message.tool_calls]
    docs_by_id: dict[str, LCDocument] = {}
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "search_documents":
            for doc in message.artifact or []:
                docs_by_id.setdefault(doc.metadata["chunk_id"], doc)

    answer = messages[-1].text if isinstance(messages[-1], AIMessage) else NO_CONTEXT_ANSWER
    return build_response(answer, "agent", list(docs_by_id.values()), messages, started_at, tool_calls)
