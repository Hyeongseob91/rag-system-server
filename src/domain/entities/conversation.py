"""
Conversation Entity

Domain Layer: 대화 히스토리 도메인 모델 (SQLAlchemy ORM)
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from src.infrastructure.database_service import Base


class Conversation(Base):
    """대화 히스토리 엔티티"""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # [{"content": "...", "source": "..."}]
    routing_decision = Column(String(50), nullable=True)  # "vectorstore" or "llm"
    processing_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 관계 설정
    user = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, question='{self.question[:30]}...')>"


class Document(Base):
    """업로드 문서 메타데이터 엔티티"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    chunk_count = Column(Integer, nullable=True)
    status = Column(String(50), default="completed")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 설정
    user = relationship("User", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, file_name='{self.file_name}')>"
