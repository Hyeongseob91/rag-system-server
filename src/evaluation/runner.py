"""
Evaluation Runner

RAG 파이프라인 평가를 오케스트레이션하는 메인 러너

책임:
1. RAG 파이프라인 실행 및 지연 시간 측정
2. Retrieval/Generation 메트릭 계산
3. 배치 평가 및 결과 집계
"""

import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.core import Settings
from src.core.profiles import ExperimentProfile, get_profile, PROFILES
from src.evaluation.schemas import (
    EvaluationRequest,
    EvaluationResult,
    RetrievalMetrics,
    GenerationMetrics,
    LatencyBreakdown,
    RetrievedDocument,
    BatchEvaluationRequest,
    BatchEvaluationResult,
    AggregatedMetrics,
)
from src.evaluation.metrics.retrieval import calculate_retrieval_metrics
from src.evaluation.metrics.generation import calculate_generation_metrics, RAGAS_AVAILABLE


@dataclass
class PipelineExecutionResult:
    """파이프라인 실행 결과"""
    answer: str
    retrieved_docs: List[RetrievedDocument]
    routing_decision: str
    latency: LatencyBreakdown


class EvaluationRunner:
    """RAG 평가 러너

    단일 질문 또는 배치 질문에 대해 RAG 파이프라인을 실행하고
    다양한 메트릭을 계산합니다.
    """

    def __init__(self, app=None, settings: Settings = None):
        """
        Args:
            app: RAGApplication 인스턴스 (None이면 생성)
            settings: 설정 객체
        """
        self._app = app
        self._settings = settings or Settings()

    def _ensure_app(self):
        """앱 인스턴스 확인 및 생성"""
        if self._app is None:
            from src.application.container import create_app
            self._app = create_app(self._settings).initialize()

    def evaluate_single(
        self,
        request: EvaluationRequest,
        include_generation_metrics: bool = True,
    ) -> EvaluationResult:
        """
        단일 질문 평가

        Args:
            request: 평가 요청
            include_generation_metrics: RAGAS 메트릭 포함 여부

        Returns:
            EvaluationResult
        """
        self._ensure_app()

        # 1. 파이프라인 실행 (지연 시간 측정)
        execution_result = self._execute_pipeline(
            question=request.question,
            profile_id=request.profile_id,
        )

        # 2. Retrieval 메트릭 계산 (relevant_doc_ids가 있을 때만)
        retrieval_metrics = None
        if request.relevant_doc_ids:
            retrieved_ids = [doc.doc_id for doc in execution_result.retrieved_docs]
            retrieval_metrics = calculate_retrieval_metrics(
                retrieved_doc_ids=retrieved_ids,
                relevant_doc_ids=request.relevant_doc_ids,
            )

        # 3. Generation 메트릭 계산 (RAGAS)
        generation_metrics = None
        if include_generation_metrics and RAGAS_AVAILABLE:
            contexts = [doc.content for doc in execution_result.retrieved_docs]
            generation_metrics = calculate_generation_metrics(
                question=request.question,
                answer=execution_result.answer,
                contexts=contexts,
                ground_truth=request.ground_truth,
                include_all_metrics=True,
            )

        return EvaluationResult(
            question=request.question,
            answer=execution_result.answer,
            ground_truth=request.ground_truth,
            retrieved_docs=execution_result.retrieved_docs,
            retrieval_metrics=retrieval_metrics,
            generation_metrics=generation_metrics,
            latency=execution_result.latency,
            profile_id=request.profile_id,
            routing_decision=execution_result.routing_decision,
        )

    def evaluate_batch(
        self,
        request: BatchEvaluationRequest,
    ) -> BatchEvaluationResult:
        """
        배치 평가

        Args:
            request: 배치 평가 요청

        Returns:
            BatchEvaluationResult (개별 결과 + 집계)
        """
        results = []
        for item in request.items:
            # 개별 항목의 profile_id가 없으면 공통 프로파일 사용
            if not item.profile_id:
                item.profile_id = request.profile_id

            result = self.evaluate_single(
                request=item,
                include_generation_metrics=request.include_generation_metrics,
            )
            results.append(result)

        # 메트릭 집계
        aggregated = self._aggregate_metrics(results)

        return BatchEvaluationResult(
            results=results,
            aggregated=aggregated,
            profile_id=request.profile_id,
        )

    def _execute_pipeline(
        self,
        question: str,
        profile_id: str = "hybrid_rerank",
    ) -> PipelineExecutionResult:
        """
        RAG 파이프라인 실행 및 지연 시간 측정

        Args:
            question: 질문
            profile_id: 프로파일 ID

        Returns:
            PipelineExecutionResult
        """
        profile = get_profile(profile_id)

        # 전체 시작 시간
        total_start = time.perf_counter()

        # 현재 구현에서는 전체 파이프라인을 한 번에 실행
        # 개별 단계 시간은 추후 워크플로우 수정으로 상세 측정 가능
        workflow_result = self._app._workflow.invoke(question)

        total_end = time.perf_counter()
        total_ms = (total_end - total_start) * 1000

        # 현재는 전체 시간만 측정, 상세 breakdown은 추정치
        # TODO: 워크플로우 수정으로 각 단계별 실제 시간 측정
        latency = LatencyBreakdown(
            total_ms=total_ms,
            query_rewrite_ms=total_ms * 0.15 if profile.use_query_rewrite else 0,
            retrieval_ms=total_ms * 0.20,
            rerank_ms=total_ms * 0.25 if profile.use_reranker else 0,
            generation_ms=total_ms * 0.40,
        )

        # 검색된 문서를 RetrievedDocument 형태로 변환
        retrieved_docs = []
        for i, content in enumerate(workflow_result.get("retrieved_docs", [])):
            retrieved_docs.append(RetrievedDocument(
                doc_id=f"doc_{i+1}",  # 현재는 임시 ID
                content=content[:500],  # 내용 일부만
                score=1.0 - (i * 0.1),  # 순위 기반 추정 점수
                rank=i + 1,
            ))

        # 라우팅 결정 추정 (retrieved_docs가 있으면 vectorstore 경로)
        routing_decision = "vectorstore" if retrieved_docs else "llm"

        return PipelineExecutionResult(
            answer=workflow_result.get("final_answer", ""),
            retrieved_docs=retrieved_docs,
            routing_decision=routing_decision,
            latency=latency,
        )

    def _aggregate_metrics(
        self,
        results: List[EvaluationResult],
    ) -> AggregatedMetrics:
        """
        개별 결과들의 메트릭 집계

        Args:
            results: 개별 평가 결과 리스트

        Returns:
            AggregatedMetrics
        """
        if not results:
            return AggregatedMetrics(total_samples=0)

        n = len(results)

        # Retrieval 메트릭 평균
        retrieval_results = [r.retrieval_metrics for r in results if r.retrieval_metrics]
        n_retrieval = len(retrieval_results)

        avg_recall_5 = sum(m.recall_at_5 for m in retrieval_results) / n_retrieval if n_retrieval else 0
        avg_recall_10 = sum(m.recall_at_10 for m in retrieval_results) / n_retrieval if n_retrieval else 0
        avg_ndcg = sum(m.ndcg_at_10 for m in retrieval_results) / n_retrieval if n_retrieval else 0
        avg_mrr = sum(m.mrr for m in retrieval_results) / n_retrieval if n_retrieval else 0
        hit_rate_5 = sum(1 for m in retrieval_results if m.hit_at_5) / n_retrieval if n_retrieval else 0
        hit_rate_10 = sum(1 for m in retrieval_results if m.hit_at_10) / n_retrieval if n_retrieval else 0

        # Generation 메트릭 평균
        gen_results = [r.generation_metrics for r in results if r.generation_metrics]
        n_gen = len(gen_results)

        avg_faith = self._safe_avg([m.faithfulness for m in gen_results if m.faithfulness is not None])
        avg_relevancy = self._safe_avg([m.answer_relevancy for m in gen_results if m.answer_relevancy is not None])
        avg_ctx_precision = self._safe_avg([m.context_precision for m in gen_results if m.context_precision is not None])
        avg_ctx_recall = self._safe_avg([m.context_recall for m in gen_results if m.context_recall is not None])

        # Latency 평균
        avg_total_latency = sum(r.latency.total_ms for r in results) / n
        avg_retrieval_latency = sum(r.latency.retrieval_ms for r in results) / n
        avg_rerank_latency = sum(r.latency.rerank_ms for r in results) / n
        avg_generation_latency = sum(r.latency.generation_ms for r in results) / n

        return AggregatedMetrics(
            avg_recall_at_5=avg_recall_5,
            avg_recall_at_10=avg_recall_10,
            avg_ndcg_at_10=avg_ndcg,
            avg_mrr=avg_mrr,
            hit_rate_at_5=hit_rate_5,
            hit_rate_at_10=hit_rate_10,
            avg_faithfulness=avg_faith,
            avg_answer_relevancy=avg_relevancy,
            avg_context_precision=avg_ctx_precision,
            avg_context_recall=avg_ctx_recall,
            avg_total_latency_ms=avg_total_latency,
            avg_retrieval_latency_ms=avg_retrieval_latency,
            avg_rerank_latency_ms=avg_rerank_latency,
            avg_generation_latency_ms=avg_generation_latency,
            total_samples=n,
        )

    def _safe_avg(self, values: List[Optional[float]]) -> Optional[float]:
        """None이 아닌 값들의 평균 계산"""
        valid = [v for v in values if v is not None]
        return sum(valid) / len(valid) if valid else None

    def get_available_profiles(self) -> List[Dict[str, Any]]:
        """사용 가능한 프로파일 목록 반환"""
        from src.core.profiles import list_profile_summaries
        return list_profile_summaries()
