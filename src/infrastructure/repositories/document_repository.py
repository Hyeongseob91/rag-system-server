"""
Document Repository

Infrastructure Layer: 문서 메타데이터 데이터 접근
"""
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.domain.entities import Document

from src.infrastructure.database_service import DatabaseService


class DocumentRepository:
    """문서 메타데이터 Repository"""

    def __init__(self, database_service: DatabaseService):
        self._db = database_service

    def create(
        self,
        user_id: int,
        file_name: str,
        chunk_count: Optional[int] = None,
        status: str = "completed"
    ) -> "Document":
        """새 문서 메타데이터 생성

        Args:
            user_id: 사용자 ID
            file_name: 파일 이름
            chunk_count: 청크 개수
            status: 상태 (pending, processing, completed, failed)

        Returns:
            생성된 Document 엔티티
        """
        from src.domain.entities.conversation import Document
        with self._db.session_scope() as session:
            document = Document(
                user_id=user_id,
                file_name=file_name,
                chunk_count=chunk_count,
                status=status
            )
            session.add(document)
            session.flush()
            session.refresh(document)
            session.expunge(document)
            return document

    def get_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List["Document"]:
        """사용자별 문서 목록 조회

        Args:
            user_id: 사용자 ID
            limit: 최대 조회 개수
            offset: 시작 위치

        Returns:
            Document 목록 (최신순)
        """
        from src.domain.entities.conversation import Document
        with self._db.session_scope() as session:
            documents = (
                session.query(Document)
                .filter(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            for doc in documents:
                session.expunge(doc)
            return documents

    def get_by_id(self, document_id: int) -> Optional["Document"]:
        """ID로 문서 조회

        Args:
            document_id: 문서 ID

        Returns:
            Document 엔티티 또는 None
        """
        from src.domain.entities.conversation import Document
        with self._db.session_scope() as session:
            document = (
                session.query(Document)
                .filter(Document.id == document_id)
                .first()
            )
            if document:
                session.expunge(document)
            return document

    def update_status(
        self,
        document_id: int,
        status: str,
        chunk_count: Optional[int] = None
    ) -> Optional["Document"]:
        """문서 상태 업데이트

        Args:
            document_id: 문서 ID
            status: 새 상태
            chunk_count: 청크 개수 (선택)

        Returns:
            업데이트된 Document 엔티티 또는 None
        """
        from src.domain.entities.conversation import Document
        with self._db.session_scope() as session:
            document = (
                session.query(Document)
                .filter(Document.id == document_id)
                .first()
            )
            if document:
                document.status = status
                if chunk_count is not None:
                    document.chunk_count = chunk_count
                session.flush()
                session.refresh(document)
                session.expunge(document)
            return document

    def count_by_user(self, user_id: int) -> int:
        """사용자별 문서 개수

        Args:
            user_id: 사용자 ID

        Returns:
            문서 개수
        """
        from src.domain.entities.conversation import Document
        with self._db.session_scope() as session:
            return (
                session.query(Document)
                .filter(Document.user_id == user_id)
                .count()
            )
