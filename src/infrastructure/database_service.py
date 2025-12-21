"""
Database Service

Infrastructure Layer: PostgreSQL 데이터베이스 연동 (SQLAlchemy)
"""
from typing import Optional, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from src.core import Settings


# SQLAlchemy Base - 모든 엔티티가 상속
Base = declarative_base()


class DatabaseService:
    """PostgreSQL 데이터베이스 서비스"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._engine = None
        self._session_maker: Optional[sessionmaker] = None

    @property
    def engine(self):
        """Lazy Loading 패턴"""
        if self._engine is None:
            self._engine = create_engine(
                self.settings.database.url,
                echo=False,  # SQL 로깅 비활성화
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True  # 연결 유효성 확인
            )
        return self._engine

    @property
    def session_maker(self) -> sessionmaker:
        """세션 팩토리"""
        if self._session_maker is None:
            self._session_maker = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        return self._session_maker

    def get_session(self) -> Session:
        """새 세션 생성"""
        return self.session_maker()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """트랜잭션 범위 세션 컨텍스트 매니저

        Usage:
            with db_service.session_scope() as session:
                session.add(entity)
                # 자동 커밋 또는 롤백
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """모든 테이블 생성 (엔티티 기반)"""
        # 엔티티 모듈 import하여 Base.metadata에 등록
        from src.domain.entities import user, conversation  # noqa: F401
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """모든 테이블 삭제 (테스트용)"""
        Base.metadata.drop_all(bind=self.engine)

    def is_ready(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def close(self) -> None:
        """데이터베이스 연결 종료"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_maker = None
