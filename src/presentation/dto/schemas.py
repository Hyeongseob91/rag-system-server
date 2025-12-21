"""
API Request/Response Schemas

Presentation Layer: HTTP API 요청/응답 스키마
Domain Entity와 분리하여 API 경계를 명확히 합니다.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============ Auth ============

class RegisterRequest(BaseModel):
    """회원가입 요청"""
    model_config = ConfigDict(json_schema_extra={"example": {"username": "user1", "password": "password123"}})
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """로그인 요청"""
    model_config = ConfigDict(json_schema_extra={"example": {"username": "user1", "password": "password123"}})
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    """인증 응답"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class UserResponse(BaseModel):
    """사용자 정보 응답"""
    id: int
    username: str
    created_at: datetime
    is_active: bool


# ============ Query ============

class QueryRequest(BaseModel):
    """질문 요청"""
    model_config = ConfigDict(json_schema_extra={"example": {"question": "RAG 시스템의 동작 원리를 설명해주세요."}})
    question: str = Field(..., min_length=1, max_length=2000)


class SourceDocument(BaseModel):
    """출처 문서"""
    content: str
    source: Optional[str] = None
    score: Optional[float] = None


class QueryResponse(BaseModel):
    """질문 응답"""
    answer: str
    sources: List[SourceDocument] = Field(default_factory=list)
    processing_time_ms: float
    cached: bool = False  # 캐시 히트 여부


# ============ Upload ============

class UploadStatus(str, Enum):
    """업로드 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """업로드 응답"""
    task_id: str
    file_name: str
    status: UploadStatus
    message: str


class UploadStatusResponse(BaseModel):
    """업로드 상태 조회 응답"""
    task_id: str
    status: UploadStatus
    file_name: str
    chunks_created: Optional[int] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None


# ============ Admin ============

class CollectionInfo(BaseModel):
    """컬렉션 정보"""
    name: str
    document_count: int
    is_ready: bool


class CollectionsResponse(BaseModel):
    """컬렉션 목록 응답"""
    collections: List[CollectionInfo]


class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    qdrant_connected: bool
    document_count: int
    version: str


class CollectionDeleteResponse(BaseModel):
    """컬렉션 삭제 응답"""
    success: bool
    message: str
    deleted_collection: str


# ============ Error ============

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    message: str
    detail: Optional[Dict[str, Any]] = None
