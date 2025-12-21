"""API Request/Response Schemas"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class QueryRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"question": "RAG 시스템의 동작 원리를 설명해주세요."}})
    question: str = Field(..., min_length=1, max_length=2000)


class SourceDocument(BaseModel):
    content: str
    source: Optional[str] = None
    score: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument] = Field(default_factory=list)
    processing_time_ms: float


class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    task_id: str
    file_name: str
    status: UploadStatus
    message: str


class UploadStatusResponse(BaseModel):
    task_id: str
    status: UploadStatus
    file_name: str
    chunks_created: Optional[int] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


class CollectionInfo(BaseModel):
    name: str
    document_count: int
    is_ready: bool


class CollectionsResponse(BaseModel):
    collections: List[CollectionInfo]


class HealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    document_count: int
    version: str


class CollectionDeleteResponse(BaseModel):
    success: bool
    message: str
    deleted_collection: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[Dict[str, Any]] = None
