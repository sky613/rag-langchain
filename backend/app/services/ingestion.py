import hashlib
import re
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status
from langchain_core.documents import Document as LCDocument
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document

SUPPORTED_TYPES = {".pdf": "pdf", ".txt": "txt", ".md": "markdown", ".markdown": "markdown"}


def normalize_text(text: str) -> str:
    # 줄바꿈 통일, NUL 제거, 연속 공백/빈 줄 축약으로 chunk 품질과 embedding 비용을 안정화한다.
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_pages(filename: str, data: bytes) -> list[LCDocument]:
    # PDF는 페이지 단위, TXT/Markdown은 단일 Document로 읽는다. 텍스트가 없는 페이지는 버린다.
    file_type = SUPPORTED_TYPES[Path(filename).suffix.lower()]

    if file_type == "pdf":
        try:
            reader = PdfReader(BytesIO(data))
            pages = [
                LCDocument(page_content=normalize_text(page.extract_text() or ""), metadata={"page": number})
                for number, page in enumerate(reader.pages, start=1)
            ]
        except PdfReadError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Invalid PDF file: {exc}") from exc
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Text file must be UTF-8 encoded") from exc
        pages = [LCDocument(page_content=normalize_text(text), metadata={})]

    return [page for page in pages if page.page_content]


def split_documents(pages: list[LCDocument], document_id: str, filename: str) -> list[LCDocument]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(pages)
    for index, chunk in enumerate(chunks):
        chunk_id = f"{document_id}:{index}"
        chunk.id = chunk_id
        chunk.metadata.update(
            document_id=document_id,
            filename=filename,
            chunk_index=index,
            chunk_id=chunk_id,
        )
    return chunks


def chunk_ids(document: Document) -> list[str]:
    return [f"{document.id}:{index}" for index in range(document.chunk_count)]


def ingest_document(db: Session, vector_store: VectorStore, filename: str, data: bytes) -> Document:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type '{suffix}'. Allowed: {', '.join(SUPPORTED_TYPES)}",
        )
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"File exceeds {settings.max_upload_mb}MB limit")

    content_hash = hashlib.sha256(data).hexdigest()
    existing = db.scalar(select(Document).where(Document.content_hash == content_hash))
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Duplicate document: identical content already uploaded as '{existing.filename}' ({existing.id})",
        )

    pages = load_pages(filename, data)
    if not pages:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "No extractable text found in document")

    document_id = str(uuid.uuid4())
    chunks = split_documents(pages, document_id, filename)
    ids = [chunk.id for chunk in chunks]
    vector_store.add_documents(chunks, ids=ids)

    document = Document(
        id=document_id,
        filename=filename,
        file_type=SUPPORTED_TYPES[suffix],
        content_hash=content_hash,
        size_bytes=len(data),
        chunk_count=len(chunks),
    )
    db.add(document)
    try:
        db.commit()
    except IntegrityError as exc:
        # 동시 업로드로 hash 충돌이 나면 방금 넣은 vector를 되돌려 고아 chunk를 남기지 않는다.
        db.rollback()
        vector_store.delete(ids=ids)
        raise HTTPException(status.HTTP_409_CONFLICT, "Duplicate document") from exc
    except Exception:
        db.rollback()
        vector_store.delete(ids=ids)
        raise

    db.refresh(document)
    return document


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())).all())


def delete_document(db: Session, vector_store: VectorStore, document_id: str) -> None:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    if document.chunk_count:
        vector_store.delete(ids=chunk_ids(document))
    db.delete(document)
    db.commit()
