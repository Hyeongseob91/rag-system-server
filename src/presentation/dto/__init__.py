"""
Data Transfer Objects (DTO)

API 요청/응답 스키마를 정의합니다.
Domain Entity와 별도로 관리하여 API 경계를 명확히 합니다.
"""
from .schemas import (
    QueryRequest, QueryResponse, SourceDocument,
    UploadResponse, UploadStatusResponse, UploadStatus,
    HealthResponse, CollectionsResponse, CollectionInfo, CollectionDeleteResponse,
    ErrorResponse,
)

__all__ = [
    "QueryRequest", "QueryResponse", "SourceDocument",
    "UploadResponse", "UploadStatusResponse", "UploadStatus",
    "HealthResponse", "CollectionsResponse", "CollectionInfo", "CollectionDeleteResponse",
    "ErrorResponse",
]
