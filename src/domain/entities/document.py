"""
Document Entity

원본 문서와 전처리 결과를 나타냅니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .chunk import Chunk


@dataclass
class RawDocument:
    """원본 문서

    파일에서 파싱한 원본 텍스트를 담습니다.

    Attributes:
        content: 전체 텍스트 내용
        source: 파일 경로
        file_type: 파일 타입
        file_name: 파일명
        metadata: 파일 메타데이터
        pages: 페이지별 텍스트 (PDF, DOCX)
        sheets: 시트별 텍스트 (XLSX)
    """
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


class DocumentMetadata(BaseModel):
    """문서 메타데이터 (API 응답용)"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    doc_id: str
    source: str
    file_name: str
    file_type: str
    file_size: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    page_count: Optional[int] = None
    sheet_count: Optional[int] = None


@dataclass
class PreprocessingResult:
    """전처리 결과

    문서 전처리 파이프라인의 결과를 담습니다.

    Attributes:
        document: 정규화된 문서
        chunks: 분할된 청크 리스트
        metadata: 문서 메타데이터
        stats: 처리 통계
        success: 성공 여부
        error: 에러 메시지
    """
    document: Optional[RawDocument]
    chunks: List[Chunk]
    metadata: Optional[DocumentMetadata]
    stats: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
