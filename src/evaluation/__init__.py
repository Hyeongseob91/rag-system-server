"""
Evaluation Module

RAG 파이프라인의 성능을 정량적으로 평가하는 모듈입니다.

Components:
- metrics/retrieval.py: Retrieval 품질 메트릭 (Recall@K, nDCG, MRR)
- metrics/generation.py: Generation 품질 메트릭 (RAGAS)
- runner.py: 평가 오케스트레이션
- schemas.py: 평가 결과 스키마
"""

from .schemas import (
    EvaluationRequest,
    EvaluationResult,
    RetrievalMetrics,
    GenerationMetrics,
    LatencyBreakdown,
    BatchEvaluationRequest,
    BatchEvaluationResult,
)
from .runner import EvaluationRunner

__all__ = [
    "EvaluationRequest",
    "EvaluationResult",
    "RetrievalMetrics",
    "GenerationMetrics",
    "LatencyBreakdown",
    "BatchEvaluationRequest",
    "BatchEvaluationResult",
    "EvaluationRunner",
]
