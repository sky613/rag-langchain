from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

if settings.database_url.startswith("sqlite:///"):
    # SQLite 파일이 들어갈 디렉터리가 없으면 연결 시 실패하므로 미리 만든다.
    Path(settings.database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)

# SQLite는 FastAPI의 threadpool에서 접근하므로 동일 thread 제한을 해제한다.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    # 모든 SQLAlchemy 모델이 상속하는 공통 Base 클래스다.
    pass


def get_db() -> Generator[Session, None, None]:
    # FastAPI dependency: 요청마다 DB 세션을 열고 응답 후 반드시 닫는다.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
