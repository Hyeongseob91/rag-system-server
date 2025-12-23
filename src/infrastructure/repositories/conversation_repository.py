"""
Conversation Repository

Infrastructure Layer: 대화 히스토리 데이터 접근
"""
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.domain.entities import Conversation

from src.infrastructure.database_service import DatabaseService


class ConversationRepository:
    """대화 히스토리 Repository"""

    def __init__(self, database_service: DatabaseService):
        self._db = database_service

    def create(
        self,
        user_id: int,
        question: str,
        answer: str,
        sources: Optional[list] = None,
        routing_decision: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> "Conversation":
        """새 대화 기록 생성

        Args:
            user_id: 사용자 ID
            question: 질문
            answer: 답변
            sources: 출처 목록
            routing_decision: 라우팅 결정 ("vectorstore" or "llm")
            processing_time_ms: 처리 시간 (밀리초)

        Returns:
            생성된 Conversation 엔티티
        """
        from src.domain.entities.conversation import Conversation
        with self._db.session_scope() as session:
            conversation = Conversation(
                user_id=user_id,
                question=question,
                answer=answer,
                sources=sources,
                routing_decision=routing_decision,
                processing_time_ms=processing_time_ms
            )
            session.add(conversation)
            session.flush()
            session.refresh(conversation)
            session.expunge(conversation)
            return conversation

    def get_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List["Conversation"]:
        """사용자별 대화 히스토리 조회

        Args:
            user_id: 사용자 ID
            limit: 최대 조회 개수
            offset: 시작 위치

        Returns:
            Conversation 목록 (최신순)
        """
        from src.domain.entities.conversation import Conversation
        with self._db.session_scope() as session:
            conversations = (
                session.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            for conv in conversations:
                session.expunge(conv)
            return conversations

    def get_by_id(self, conversation_id: int) -> Optional["Conversation"]:
        """ID로 대화 조회

        Args:
            conversation_id: 대화 ID

        Returns:
            Conversation 엔티티 또는 None
        """
        from src.domain.entities.conversation import Conversation
        with self._db.session_scope() as session:
            conversation = (
                session.query(Conversation)
                .filter(Conversation.id == conversation_id)
                .first()
            )
            if conversation:
                session.expunge(conversation)
            return conversation

    def count_by_user(self, user_id: int) -> int:
        """사용자별 대화 개수

        Args:
            user_id: 사용자 ID

        Returns:
            대화 개수
        """
        from src.domain.entities.conversation import Conversation
        with self._db.session_scope() as session:
            return (
                session.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .count()
            )
