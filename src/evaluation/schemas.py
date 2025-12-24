"""
Evaluation Schemas

평가 요청/응답을 위한 Pydantic 모델 정의
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RetrievalMetrics(BaseModel):
    """검색 품질 메트릭"""
    recall_at_5: float = Field(..., description="Top-5 중 정답 문서 포함률", ge=0, le=1)
    recall_at_10: float = Field(..., description="Top-10 중 정답 문서 포함률", ge=0, le=1)
    ndcg_at_10: float = Field(..., description="순위 가중 관련성 점수", ge=0, le=1)
    mrr: float = Field(..., description="첫 정답 문서의 역순위", ge=0, le=1)
    hit_at_5: bool = Field(..., description="Top-5 내 정답 존재 여부")
    hit_at_10: bool = Field(..., description="Top-10 내 정답 존재 여부")


class GenerationMetrics(BaseModel):
    """생성 품질 메트릭 (RAGAS)"""
    faithfulness: Optional[float] = Field(None, description="답변이 Context에 충실한지", ge=0, le=1)
    answer_relevancy: Optional[float] = Field(None, description="답변이 질문에 적합한지", ge=0, le=1)
    context_precision: Optional[float] = Field(None, description="검색된 문서의 정밀도", ge=0, le=1)
    context_recall: Optional[float] = Field(None, description="필요 정보 검색 완성도", ge=0, le=1)


class LatencyBreakdown(BaseModel):
    """지연 시간 상세"""
    total_ms: float = Field(..., description="전체 처리 시간 (ms)")
    query_rewrite_ms: float = Field(0.0, description="쿼리 최적화 시간 (ms)")
    retrieval_ms: float = Field(0.0, description="벡터 검색 시간 (ms)")
    rerank_ms: float = Field(0.0, description="Reranking 시간 (ms)")
    generation_ms: float = Field(0.0, description="LLM 응답 생성 시간 (ms)")


class EvaluationRequest(BaseModel):
    """단일 평가 요청"""
    question: str = Field(..., description="평가할 질문")
    ground_truth: Optional[str] = Field(None, description="정답 (Generation 평가용)")
    relevant_doc_ids: Optional[List[str]] = Field(None, description="관련 문서 ID 목록 (Retrieval 평가용)")
    profile_id: str = Field("hybrid_rerank", description="사용할 실험 프로파일 ID")


class RetrievedDocument(BaseModel):
    """검색된 문서 정보"""
    doc_id: str = Field(..., description="문서 ID")
    content: str = Field(..., description="문서 내용")
    score: float = Field(..., description="검색 점수")
    rank: int = Field(..., description="검색 순위 (1부터 시작)")


class EvaluationResult(BaseModel):
    """단일 평가 결과"""
    question: str = Field(..., description="평가한 질문")
    answer: str = Field(..., description="생성된 답변")
    ground_truth: Optional[str] = Field(None, description="정답")

    # 검색 결과
    retrieved_docs: List[RetrievedDocument] = Field(default_factory=list, description="검색된 문서들")

    # 메트릭
    retrieval_metrics: Optional[RetrievalMetrics] = Field(None, description="검색 품질 메트릭")
    generation_metrics: Optional[GenerationMetrics] = Field(None, description="생성 품질 메트릭")
    latency: LatencyBreakdown = Field(..., description="지연 시간 상세")

    # 메타데이터
    profile_id: str = Field(..., description="사용된 프로파일 ID")
    routing_decision: str = Field("vectorstore", description="라우팅 결정 (vectorstore/llm)")


class BatchEvaluationRequest(BaseModel):
    """배치 평가 요청"""
    items: List[EvaluationRequest] = Field(..., description="평가할 항목들")
    profile_id: str = Field("hybrid_rerank", description="공통 프로파일 ID (개별 항목 설정 우선)")
    include_generation_metrics: bool = Field(True, description="RAGAS 메트릭 포함 여부 (시간 많이 소요)")


class AggregatedMetrics(BaseModel):
    """집계된 메트릭"""
    # Retrieval 평균
    avg_recall_at_5: float = Field(0.0, ge=0, le=1)
    avg_recall_at_10: float = Field(0.0, ge=0, le=1)
    avg_ndcg_at_10: float = Field(0.0, ge=0, le=1)
    avg_mrr: float = Field(0.0, ge=0, le=1)
    hit_rate_at_5: float = Field(0.0, ge=0, le=1)
    hit_rate_at_10: float = Field(0.0, ge=0, le=1)

    # Generation 평균
    avg_faithfulness: Optional[float] = Field(None, ge=0, le=1)
    avg_answer_relevancy: Optional[float] = Field(None, ge=0, le=1)
    avg_context_precision: Optional[float] = Field(None, ge=0, le=1)
    avg_context_recall: Optional[float] = Field(None, ge=0, le=1)

    # Latency 평균
    avg_total_latency_ms: float = Field(0.0, ge=0)
    avg_retrieval_latency_ms: float = Field(0.0, ge=0)
    avg_rerank_latency_ms: float = Field(0.0, ge=0)
    avg_generation_latency_ms: float = Field(0.0, ge=0)

    # 샘플 수
    total_samples: int = Field(0, ge=0)


class BatchEvaluationResult(BaseModel):
    """배치 평가 결과"""
    results: List[EvaluationResult] = Field(..., description="개별 평가 결과들")
    aggregated: AggregatedMetrics = Field(..., description="집계된 메트릭")
    profile_id: str = Field(..., description="사용된 프로파일 ID")
