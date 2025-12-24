"""
Generation Metrics (RAGAS Integration)

LLM 생성 품질을 측정하는 RAGAS 기반 메트릭

메트릭 설명:
- Faithfulness: 생성된 답변이 제공된 Context에만 기반하는지 (환각 방지)
- Answer Relevancy: 답변이 질문에 적절하게 대응하는지
- Context Precision: 검색된 문서들이 답변에 얼마나 기여했는지
- Context Recall: 필요한 정보가 Context에 모두 포함되어 있는지

주의:
- RAGAS는 LLM API 호출이 필요하므로 비용이 발생합니다
- 평가당 약 4-8개의 LLM 호출이 발생할 수 있습니다
"""

import asyncio
from typing import Optional, List
from src.evaluation.schemas import GenerationMetrics

# RAGAS imports (optional - graceful fallback if not installed)
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from datasets import Dataset
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False


class GenerationEvaluator:
    """RAGAS 기반 Generation 품질 평가기"""

    def __init__(self, llm_model: str = "gpt-4o-mini"):
        """
        Args:
            llm_model: RAGAS 평가에 사용할 LLM 모델
        """
        self.llm_model = llm_model
        self._check_availability()

    def _check_availability(self) -> None:
        """RAGAS 사용 가능 여부 확인"""
        if not RAGAS_AVAILABLE:
            print("[Warning] RAGAS not installed. Install with: pip install ragas")
            print("[Warning] Generation metrics will return None values")

    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        include_all_metrics: bool = True,
    ) -> GenerationMetrics:
        """
        동기식 평가 실행

        Args:
            question: 원본 질문
            answer: 생성된 답변
            contexts: 검색된 문서 내용들
            ground_truth: 정답 (context_recall 평가에 필요)
            include_all_metrics: 모든 메트릭 계산 여부 (False면 faithfulness만)

        Returns:
            GenerationMetrics 객체
        """
        if not RAGAS_AVAILABLE:
            return GenerationMetrics()

        try:
            return asyncio.run(
                self.evaluate_async(
                    question=question,
                    answer=answer,
                    contexts=contexts,
                    ground_truth=ground_truth,
                    include_all_metrics=include_all_metrics,
                )
            )
        except Exception as e:
            print(f"[Error] RAGAS evaluation failed: {e}")
            return GenerationMetrics()

    async def evaluate_async(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        include_all_metrics: bool = True,
    ) -> GenerationMetrics:
        """
        비동기식 평가 실행

        Args:
            question: 원본 질문
            answer: 생성된 답변
            contexts: 검색된 문서 내용들
            ground_truth: 정답 (context_recall 평가에 필요)
            include_all_metrics: 모든 메트릭 계산 여부

        Returns:
            GenerationMetrics 객체
        """
        if not RAGAS_AVAILABLE:
            return GenerationMetrics()

        try:
            # RAGAS 데이터셋 형식으로 변환
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }

            # ground_truth가 있으면 추가
            if ground_truth:
                data["ground_truth"] = [ground_truth]

            dataset = Dataset.from_dict(data)

            # 평가할 메트릭 선택
            metrics_to_evaluate = [faithfulness]
            if include_all_metrics:
                metrics_to_evaluate.append(answer_relevancy)
                metrics_to_evaluate.append(context_precision)
                if ground_truth:
                    metrics_to_evaluate.append(context_recall)

            # RAGAS 평가 실행
            result = evaluate(dataset, metrics=metrics_to_evaluate)

            # 결과 파싱
            return GenerationMetrics(
                faithfulness=self._safe_get(result, "faithfulness"),
                answer_relevancy=self._safe_get(result, "answer_relevancy"),
                context_precision=self._safe_get(result, "context_precision"),
                context_recall=self._safe_get(result, "context_recall"),
            )

        except Exception as e:
            print(f"[Error] RAGAS async evaluation failed: {e}")
            return GenerationMetrics()

    def _safe_get(self, result: dict, key: str) -> Optional[float]:
        """안전하게 결과값 추출"""
        try:
            value = result.get(key)
            if value is not None:
                # RAGAS 결과가 리스트일 수 있음
                if isinstance(value, list) and len(value) > 0:
                    return float(value[0])
                return float(value)
            return None
        except (TypeError, ValueError, IndexError):
            return None


def calculate_generation_metrics(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None,
    include_all_metrics: bool = True,
) -> GenerationMetrics:
    """
    Generation 메트릭 계산 헬퍼 함수

    Args:
        question: 원본 질문
        answer: 생성된 답변
        contexts: 검색된 문서 내용들
        ground_truth: 정답 (optional)
        include_all_metrics: 모든 메트릭 계산 여부

    Returns:
        GenerationMetrics 객체
    """
    evaluator = GenerationEvaluator()
    return evaluator.evaluate(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth,
        include_all_metrics=include_all_metrics,
    )


def calculate_generation_metrics_simple(
    question: str,
    answer: str,
    contexts: List[str],
) -> GenerationMetrics:
    """
    간소화된 Generation 메트릭 계산 (Faithfulness만)

    RAGAS 호출 비용을 줄이기 위해 Faithfulness만 계산

    Args:
        question: 원본 질문
        answer: 생성된 답변
        contexts: 검색된 문서 내용들

    Returns:
        GenerationMetrics 객체 (faithfulness만 값이 있음)
    """
    evaluator = GenerationEvaluator()
    return evaluator.evaluate(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=None,
        include_all_metrics=False,
    )
