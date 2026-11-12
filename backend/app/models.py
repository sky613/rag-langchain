import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    # DB에 저장되는 시간은 timezone-aware UTC datetime으로 통일한다.
    return datetime.now(timezone.utc)


class Document(Base):
    # 업로드된 문서의 metadata. 실제 chunk와 embedding은 Chroma에 저장된다.
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 동일 내용 재업로드를 막기 위한 원본 바이트의 SHA-256 hash다.
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    # chunk ID는 "{document_id}:{index}" 규칙이라 개수만으로 Chroma 삭제 대상을 복원할 수 있다.
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
