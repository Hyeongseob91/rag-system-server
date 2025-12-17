"""Pydantic Models for Structured Output"""
from typing import List, Literal
from pydantic import BaseModel, Field


class RouteQuery(BaseModel):
    datasource: Literal["vectorstore", "llm"] = Field(
        ..., description="외부 정보 검색이 필요하면 'vectorstore', 단순 대화나 일반 상식은 'llm'"
    )


class RewriteResult(BaseModel):
    queries: List[str] = Field(description="검색 엔진에 최적화된, 3개 내외의 재작성된 쿼리 리스트")
