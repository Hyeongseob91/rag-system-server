"""
LLM Output Models

LLM의 구조화된 출력을 위한 Pydantic 모델입니다.
"""
from typing import List, Literal
from pydantic import BaseModel, Field


class RouteQuery(BaseModel):
    """라우팅 결정 스키마

    질문이 외부 정보 검색이 필요한지 판단합니다.
    - vectorstore: RAG 검색 필요 (회사 규정, 특정 사실 등)
    - llm: 검색 불필요 (일반 상식, 인사, 요약 등)
    """
    datasource: Literal["vectorstore", "llm"] = Field(
        ..., description="외부 정보 검색이 필요하면 'vectorstore', 단순 대화나 일반 상식은 'llm'"
    )


class RewriteResult(BaseModel):
    """쿼리 리라이트 결과 스키마

    사용자 질문을 검색에 최적화된 쿼리로 변환합니다.
    다각도의 쿼리로 검색 재현율을 높입니다.
    """
    queries: List[str] = Field(
        description="검색 엔진에 최적화된, 3개 내외의 재작성된 쿼리 리스트"
    )
