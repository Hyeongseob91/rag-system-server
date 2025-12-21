"""
Domain Entities

도메인의 핵심 데이터 구조를 정의합니다.
- Chunk: 문서 청크
- RawDocument: 원본 문서
- Models: LLM 출력 스키마
- User: 사용자 (SQLAlchemy ORM)
- Conversation: 대화 히스토리 (SQLAlchemy ORM)
- Document: 업로드 문서 메타데이터 (SQLAlchemy ORM)
"""
from .chunk import Chunk, ChunkMetadata
from .document import RawDocument, DocumentMetadata, PreprocessingResult
from .models import RewriteResult, RouteQuery
from .user import User
from .conversation import Conversation, Document

__all__ = [
    "Chunk", "ChunkMetadata",
    "RawDocument", "DocumentMetadata", "PreprocessingResult",
    "RewriteResult", "RouteQuery",
    "User", "Conversation", "Document",
]
