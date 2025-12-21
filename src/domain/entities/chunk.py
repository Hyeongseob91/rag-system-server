"""
Chunk Entity

문서를 분할한 청크 단위를 나타냅니다.
청크는 벡터 DB에 저장되는 최소 단위입니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field, ConfigDict


@dataclass
class Chunk:
    """문서 청크

    문서를 의미 단위로 분할한 결과입니다.
    벡터 DB에 저장되는 최소 검색 단위입니다.

    Attributes:
        content: 청크 텍스트 내용
        chunk_id: 청크 고유 ID (UUID)
        chunk_index: 문서 내 청크 순서
        doc_id: 원본 문서 ID
        source: 파일 경로
        file_name: 파일명
        file_type: 파일 타입 (pdf, docx 등)
        metadata: 추가 메타데이터
    """
    content: str
    chunk_id: str
    chunk_index: int
    doc_id: str
    source: str
    file_name: str
    file_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """문자 수"""
        return len(self.content)

    def to_qdrant_payload(self) -> Dict[str, Any]:
        """Qdrant 저장용 payload로 변환"""
        return {
            "content": self.content,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "total_chunks": self.metadata.get("total_chunks", 1),
            "source": self.source,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "char_count": self.char_count,
            "page_number": self.metadata.get("page_number"),
            "sheet_name": self.metadata.get("sheet_name"),
            "created_at": datetime.now().isoformat(),
        }


class ChunkMetadata(BaseModel):
    """청크 메타데이터 (API 응답용)"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    chunk_id: str
    doc_id: str
    chunk_index: int
    total_chunks: int
    source: str
    file_name: str
    file_type: str
    char_count: int
    page_number: Optional[int] = None
    sheet_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
