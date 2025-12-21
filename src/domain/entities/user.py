"""
User Entity

Domain Layer: 사용자 도메인 모델 (SQLAlchemy ORM)
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from src.infrastructure.database_service import Base


class User(Base):
    """사용자 엔티티"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # 관계 설정
    conversations = relationship("Conversation", back_populates="user")
    documents = relationship("Document", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
