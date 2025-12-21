"""Preprocessing Schemas"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


@dataclass
class RawDocument:
    content: str
    source: str
    file_type: str
    file_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages: Optional[List[str]] = None
    sheets: Optional[Dict[str, str]] = None

    def __post_init__(self):
        if self.pages is None:
            self.pages = []
        if self.sheets is None:
            self.sheets = {}


@dataclass
class Chunk:
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
        return len(self.content)

    def to_weaviate_object(self) -> Dict[str, Any]:
        """Weaviate용 객체 변환 (Legacy)"""
        created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
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
            "created_at": created_at,
        }

    def to_qdrant_payload(self) -> Dict[str, Any]:
        """Qdrant용 payload 변환"""
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


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    doc_id: str
    source: str
    file_name: str
    file_type: str
    file_size: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    page_count: Optional[int] = None
    sheet_count: Optional[int] = None


class ChunkMetadata(BaseModel):
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


@dataclass
class PreprocessingResult:
    document: Optional[RawDocument]
    chunks: List[Chunk]
    metadata: Optional[DocumentMetadata]
    stats: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
