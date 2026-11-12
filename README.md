# rag-langchain

LangChain 기반 문서 RAG 애플리케이션 MVP입니다. PDF/TXT/Markdown 문서를 업로드하면 chunk 단위로 Chroma에 저장하고, 질문에 대해 검색된 chunk만 근거로 답변하며 citation(chunk ID)을 함께 반환합니다.

- **RAG 모드 (기본)**: 항상 검색 → 답변하는 결정적 2-Step RAG. 순수 Python / LangGraph 구현과의 벤치마크 기준선.
- **Agent 모드 (선택)**: LangChain `create_agent`로 만든 tool-calling Agent가 `search_documents` / `list_documents` 사용 여부를 스스로 결정.

OpenAI API Key는 백엔드(`backend/.env`)에서만 사용합니다. 프론트엔드나 `VITE_*` 환경변수에 넣지 마세요.

## Architecture

```text
React + TypeScript (Vite, Tailwind, Zustand)
  ↓  REST
FastAPI
  ├── routes/documents.py   POST/GET/DELETE /api/documents
  ├── routes/chat.py        POST /api/chat
  └── services/
      ├── ingestion.py  Loader(pypdf / UTF-8) → normalize → RecursiveCharacterTextSplitter
      │                 → Chroma(OpenAIEmbeddings) + SQLite metadata, SHA-256 중복 검사, 삭제
      ├── rag.py        Retriever → ChatPromptTemplate | ChatOpenAI → Answer + Citations
      ├── agent.py      create_agent + tools(search_documents, list_documents)
      └── llm.py        ChatOpenAI / Chroma 인스턴스 (lru_cache)
```

2-Step RAG 흐름 (`services/rag.py`):

```text
Question → VectorStoreRetriever(k) → format_context → ChatPromptTemplate | ChatOpenAI
        → answer + sources + cited_chunk_ids + usage + latency + cost
```

설계 포인트:

- **Chunk ID**: `{document_id}:{chunk_index}` 규칙. Chroma ID와 metadata에 동일하게 저장해 문서 삭제 시 SQLite의 `chunk_count`만으로 vector를 지울 수 있습니다.
- **근거 없는 답변 방지**: 검색 결과가 없으면 LLM을 호출하지 않고 고정 메시지를 반환합니다. 프롬프트는 context 밖 사실과 없는 citation을 금지하고, 응답의 `cited_chunk_ids`는 실제 제공된 chunk ID와 교차 검증된 것만 남깁니다.
- **Agent sources**: `search_documents`는 `content_and_artifact` tool이라, 응답 `sources`는 모델 출력이 아닌 실제 검색된 Document에서 만들어집니다.
- **재사용/테스트 용이성**: `answer_with_rag(question, retriever=None, llm=None)`, `answer_with_agent(...)`는 retriever/LLM을 주입받을 수 있어 외부 호출 없이 fake 모델로 검증할 수 있습니다.
- LangGraph graph 코드는 작성하지 않았습니다. `create_agent`가 내부적으로 LangGraph를 사용하므로 `langgraph`는 transitive dependency로 설치됩니다.

## Dependency versions

Backend (Python 3.11+, `backend/requirements.txt`):

| Package | Version |
|---|---|
| fastapi | 0.162.5 |
| uvicorn[standard] | 0.54.0 |
| pydantic-settings | 2.16.2 |
| python-multipart | 0.0.33 (업로드 multipart 파싱) |
| sqlalchemy | 2.1.8 |
| langchain | 1.5.0 (`create_agent`) |
| langchain-core | 1.8.0 |
| langchain-openai | 1.7.4 |
| langchain-chroma | 1.1.0 |
| langchain-text-splitters | 1.1.3 |
| chromadb | 1.5.9 |
| pypdf | 7.0.1 |

Python 3.11 venv에 위 버전 조합으로 설치 및 import 호환성을 확인했습니다 (transitive: langgraph 1.2.20, openai 3.49.0).

Frontend: React, TypeScript, Vite, Tailwind CSS, Zustand, react-markdown, lucide-react (`frontend/package.json`, `pnpm-lock.yaml`).

## 환경변수

`backend/.env.example`을 `backend/.env`로 복사하고 `OPENAI_API_KEY`를 설정합니다.

```env
OPENAI_API_KEY=your-openai-api-key
CHAT_MODEL=gpt-4.1-mini
EMBEDDING_MODEL=text-embedding-3-small
INPUT_COST_PER_MILLION=0.40
OUTPUT_COST_PER_MILLION=1.60
DATABASE_URL=sqlite:///./data/rag.db
CHROMA_DIR=./data/chroma
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
RETRIEVAL_K=4
MAX_UPLOAD_MB=20
```

`estimated_cost_usd`는 `INPUT/OUTPUT_COST_PER_MILLION` 단가로 계산한 chat 모델 비용 추정치입니다(query embedding 비용 제외). 모델을 바꾸면 단가도 함께 갱신하세요.

임베딩 모델을 바꾸면 기존 Chroma 데이터와 차원이 달라지므로 `backend/data/`를 지우고 문서를 다시 업로드해야 합니다.

## 실행

Docker:

```bash
docker compose up --build
```

로컬:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```bash
cd frontend
corepack enable
corepack pnpm install
corepack pnpm dev
```

- 프론트엔드: http://localhost:5173
- 백엔드: http://localhost:8000 (API 문서: `/docs`)

데이터는 `backend/data/`(SQLite `rag.db`, Chroma `chroma/`)에 저장됩니다.

## API

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/documents` | multipart `file` 업로드. 415 지원하지 않는 형식, 400 빈 파일, 413 용량 초과, 409 중복, 422 텍스트 없음/파싱 실패 |
| GET | `/api/documents` | 문서 목록 |
| DELETE | `/api/documents/{id}` | 문서와 Chroma chunk 삭제. 404 없음 |
| POST | `/api/chat` | `{"question": "...", "mode": "rag" \| "agent"}` |
| GET | `/api/health` | 헬스 체크 |

`POST /api/chat` 응답 예시:

```json
{
  "answer": "환불은 구매 후 14일 이내 가능합니다 [3f2c...:2].",
  "mode": "rag",
  "sources": [
    {"chunk_id": "3f2c...:2", "document_id": "3f2c...", "filename": "policy.pdf",
     "page": 3, "chunk_index": 2, "snippet": "..."}
  ],
  "cited_chunk_ids": ["3f2c...:2"],
  "tool_calls": [],
  "usage": {"input_tokens": 812, "output_tokens": 54, "total_tokens": 866},
  "latency_ms": 1432,
  "estimated_cost_usd": 0.000411
}
```

오류: `OPENAI_API_KEY` 미설정 시 500, OpenAI 호출 실패 시 502.

## 제한 사항

- 대화 이력은 서버에 저장하지 않으며, 각 질문은 독립적으로 처리됩니다.
- 스캔 이미지 PDF(OCR 필요)는 텍스트가 추출되지 않아 422를 반환합니다.
- TXT/Markdown은 UTF-8만 지원합니다.
# rag-langgraph
# rag-langchain
