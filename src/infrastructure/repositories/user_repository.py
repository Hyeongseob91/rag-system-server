"""
User Repository

Infrastructure Layer: 사용자 데이터 접근
"""
from typing import Optional

from src.domain.entities import User
from src.infrastructure.database_service import DatabaseService


class UserRepository:
    """사용자 Repository"""

    def __init__(self, database_service: DatabaseService):
        self._db = database_service

    def create(self, username: str, password_hash: str) -> User:
        """새 사용자 생성

        Args:
            username: 사용자 이름
            password_hash: 해시된 비밀번호

        Returns:
            생성된 User 엔티티
        """
        with self._db.session_scope() as session:
            user = User(username=username, password_hash=password_hash)
            session.add(user)
            session.flush()  # ID 생성을 위해 flush
            session.refresh(user)
            # detach from session
            session.expunge(user)
            return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회

        Args:
            user_id: 사용자 ID

        Returns:
            User 엔티티 또는 None
        """
        with self._db.session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.expunge(user)
            return user

    def get_by_username(self, username: str) -> Optional[User]:
        """사용자 이름으로 조회

        Args:
            username: 사용자 이름

        Returns:
            User 엔티티 또는 None
        """
        with self._db.session_scope() as session:
            user = session.query(User).filter(User.username == username).first()
            if user:
                session.expunge(user)
            return user

    def exists(self, username: str) -> bool:
        """사용자 이름 존재 여부 확인

        Args:
            username: 사용자 이름

        Returns:
            존재 여부
        """
        with self._db.session_scope() as session:
            return session.query(User).filter(User.username == username).count() > 0
