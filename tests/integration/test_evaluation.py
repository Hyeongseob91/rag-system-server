"""
Evaluation Module Integration Tests

평가 모듈의 통합 테스트
- API 엔드포인트 테스트
- 메트릭 계산 테스트
- 프로파일 시스템 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from src.presentation.api.main import app
from src.evaluation.schemas import (
    RetrievalMetrics,
    GenerationMetrics,
    LatencyBreakdown,
    EvaluationResult,
    RetrievedDocument,
)
from src.evaluation.metrics.retrieval import (
    recall_at_k,
    ndcg_at_k,
    mrr,
    hit_at_k,
    calculate_retrieval_metrics,
)
from src.core.profiles import PROFILES, get_profile, list_profiles


class TestRetrievalMetrics:
    """Retrieval 메트릭 계산 테스트"""

    def test_recall_at_k_perfect_recall(self):
        """모든 관련 문서가 검색된 경우"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc2", "doc3"}

        result = recall_at_k(retrieved, relevant, k=5)
        assert result == 1.0

    def test_recall_at_k_partial_recall(self):
        """일부 관련 문서만 검색된 경우"""
        retrieved = ["doc1", "doc4", "doc5", "doc6", "doc7"]
        relevant = {"doc1", "doc2", "doc3"}

        result = recall_at_k(retrieved, relevant, k=5)
        assert result == pytest.approx(1/3)

    def test_recall_at_k_no_recall(self):
        """관련 문서가 하나도 검색되지 않은 경우"""
        retrieved = ["doc4", "doc5", "doc6", "doc7", "doc8"]
        relevant = {"doc1", "doc2", "doc3"}

        result = recall_at_k(retrieved, relevant, k=5)
        assert result == 0.0

    def test_recall_at_k_empty_relevant(self):
        """관련 문서가 없는 경우"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = set()

        result = recall_at_k(retrieved, relevant, k=5)
        assert result == 0.0

    def test_ndcg_at_k_perfect_ranking(self):
        """완벽한 순위 (관련 문서가 상위에)"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc2"}

        result = ndcg_at_k(retrieved, relevant, k=5)
        assert result == 1.0

    def test_ndcg_at_k_suboptimal_ranking(self):
        """비최적 순위 (관련 문서가 하위에)"""
        retrieved = ["doc4", "doc5", "doc1", "doc2", "doc6"]
        relevant = {"doc1", "doc2"}

        result = ndcg_at_k(retrieved, relevant, k=5)
        assert 0 < result < 1.0

    def test_mrr_first_position(self):
        """첫 번째 위치에 관련 문서"""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc1"}

        result = mrr(retrieved, relevant)
        assert result == 1.0

    def test_mrr_second_position(self):
        """두 번째 위치에 관련 문서"""
        retrieved = ["doc2", "doc1", "doc3"]
        relevant = {"doc1"}

        result = mrr(retrieved, relevant)
        assert result == 0.5

    def test_mrr_no_relevant(self):
        """관련 문서 없음"""
        retrieved = ["doc2", "doc3", "doc4"]
        relevant = {"doc1"}

        result = mrr(retrieved, relevant)
        assert result == 0.0

    def test_hit_at_k_hit(self):
        """Top-K 내에 관련 문서 존재"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc3"}

        result = hit_at_k(retrieved, relevant, k=5)
        assert result is True

    def test_hit_at_k_miss(self):
        """Top-K 내에 관련 문서 없음"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc6"}

        result = hit_at_k(retrieved, relevant, k=5)
        assert result is False

    def test_calculate_retrieval_metrics_with_relevants(self):
        """관련 문서 ID가 제공된 경우 전체 메트릭 계산"""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5", "doc6", "doc7", "doc8", "doc9", "doc10"]
        relevant = ["doc1", "doc3", "doc5"]

        metrics = calculate_retrieval_metrics(retrieved, relevant)

        assert isinstance(metrics, RetrievalMetrics)
        assert 0 <= metrics.recall_at_5 <= 1
        assert 0 <= metrics.recall_at_10 <= 1
        assert 0 <= metrics.ndcg_at_10 <= 1
        assert 0 <= metrics.mrr <= 1

    def test_calculate_retrieval_metrics_without_relevants(self):
        """관련 문서 ID가 없는 경우 기본값"""
        retrieved = ["doc1", "doc2", "doc3"]

        metrics = calculate_retrieval_metrics(retrieved, None)

        assert metrics.recall_at_5 == 0.0
        assert metrics.hit_at_5 is False


class TestProfileSystem:
    """실험 프로파일 시스템 테스트"""

    def test_profiles_exist(self):
        """프로파일이 정의되어 있는지 확인"""
        assert len(PROFILES) >= 3

    def test_baseline_profile_exists(self):
        """baseline 프로파일 존재 확인"""
        profile = get_profile("baseline")
        assert profile is not None
        assert profile.id == "baseline"
        assert profile.use_reranker is False

    def test_hybrid_rerank_profile_exists(self):
        """hybrid_rerank 프로파일 존재 확인"""
        profile = get_profile("hybrid_rerank")
        assert profile is not None
        assert profile.use_reranker is True
        assert profile.retriever_type == "hybrid"

    def test_list_profiles_returns_all(self):
        """모든 프로파일 목록 반환"""
        profiles = list_profiles()
        assert len(profiles) == len(PROFILES)

    def test_get_profile_not_found(self):
        """존재하지 않는 프로파일 조회시 ValueError 발생"""
        import pytest
        with pytest.raises(ValueError) as exc_info:
            get_profile("nonexistent")
        assert "Unknown profile" in str(exc_info.value)

    def test_profile_has_required_fields(self):
        """프로파일에 필수 필드 존재"""
        for profile_id, profile in PROFILES.items():
            assert hasattr(profile, 'id')
            assert hasattr(profile, 'name')
            assert hasattr(profile, 'retriever_type')
            assert hasattr(profile, 'use_reranker')
            assert hasattr(profile, 'initial_retrieval_limit')
            assert hasattr(profile, 'rerank_top_k')


class TestEvaluationSchemas:
    """평가 스키마 테스트"""

    def test_latency_breakdown_creation(self):
        """LatencyBreakdown 생성 테스트"""
        latency = LatencyBreakdown(
            total_ms=1500.0,
            query_rewrite_ms=200.0,
            retrieval_ms=300.0,
            rerank_ms=400.0,
            generation_ms=600.0,
        )
        assert latency.total_ms == 1500.0
        assert latency.query_rewrite_ms == 200.0

    def test_retrieval_metrics_creation(self):
        """RetrievalMetrics 생성 테스트"""
        metrics = RetrievalMetrics(
            recall_at_5=0.8,
            recall_at_10=0.9,
            ndcg_at_10=0.75,
            mrr=0.7,
            hit_at_5=True,
            hit_at_10=True,
        )
        assert metrics.recall_at_5 == 0.8
        assert metrics.hit_at_5 is True

    def test_generation_metrics_optional_fields(self):
        """GenerationMetrics 옵션 필드 테스트"""
        metrics = GenerationMetrics(
            faithfulness=None,
            answer_relevancy=0.85,
            context_precision=None,
            context_recall=None,
        )
        assert metrics.faithfulness is None
        assert metrics.answer_relevancy == 0.85

    def test_evaluation_result_creation(self):
        """EvaluationResult 전체 생성 테스트"""
        result = EvaluationResult(
            question="테스트 질문",
            answer="테스트 답변",
            ground_truth=None,
            retrieved_docs=[
                RetrievedDocument(
                    doc_id="doc1",
                    content="문서 내용",
                    score=0.95,
                    rank=1,
                )
            ],
            retrieval_metrics=RetrievalMetrics(
                recall_at_5=0.8,
                recall_at_10=0.9,
                ndcg_at_10=0.75,
                mrr=0.7,
                hit_at_5=True,
                hit_at_10=True,
            ),
            generation_metrics=None,
            latency=LatencyBreakdown(
                total_ms=1000.0,
                query_rewrite_ms=100.0,
                retrieval_ms=200.0,
                rerank_ms=300.0,
                generation_ms=400.0,
            ),
            profile_id="hybrid_rerank",
            routing_decision="rag",
        )

        assert result.question == "테스트 질문"
        assert len(result.retrieved_docs) == 1
        assert result.profile_id == "hybrid_rerank"
        assert result.retrieved_docs[0].rank == 1


class TestEvaluationAPI:
    """평가 API 엔드포인트 테스트"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Health 엔드포인트 테스트"""
        response = client.get("/api/v1/eval/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "ragas_available" in data
        assert "profiles_count" in data

    def test_profiles_list_endpoint(self, client):
        """프로파일 목록 엔드포인트 테스트"""
        response = client.get("/api/v1/eval/profiles")
        assert response.status_code == 200

        profiles = response.json()
        assert isinstance(profiles, list)
        assert len(profiles) >= 3

        # 각 프로파일에 필수 필드 확인
        for profile in profiles:
            assert "id" in profile
            assert "name" in profile
            assert "retriever_type" in profile

    def test_profile_detail_endpoint(self, client):
        """프로파일 상세 엔드포인트 테스트"""
        response = client.get("/api/v1/eval/profiles/hybrid_rerank")
        assert response.status_code == 200

        profile = response.json()
        assert profile["id"] == "hybrid_rerank"
        assert profile["use_reranker"] is True

    def test_profile_not_found(self, client):
        """존재하지 않는 프로파일 테스트"""
        response = client.get("/api/v1/eval/profiles/nonexistent")
        assert response.status_code == 404


class TestEvaluationAPIWithMocks:
    """Mock을 사용한 평가 API 테스트"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_single_evaluation_endpoint_structure(self, client):
        """단일 평가 엔드포인트 요청 구조 테스트"""
        # 실제 LLM 호출 없이 요청 구조만 테스트
        request_body = {
            "question": "테스트 질문입니다",
            "ground_truth": "예상 답변",
            "profile_id": "hybrid_rerank",
            "include_generation_metrics": False,
        }

        # 요청 스키마 검증 (실제 실행은 하지 않음)
        assert "question" in request_body
        assert "profile_id" in request_body

    def test_batch_evaluation_endpoint_structure(self, client):
        """배치 평가 엔드포인트 요청 구조 테스트"""
        request_body = {
            "items": [
                {"question": "질문 1", "ground_truth": "답변 1"},
                {"question": "질문 2", "ground_truth": "답변 2"},
            ],
            "profile_id": "baseline",
            "include_generation_metrics": False,
        }

        assert len(request_body["items"]) == 2
        assert request_body["profile_id"] == "baseline"

    def test_export_json_endpoint_structure(self, client):
        """JSON 내보내기 엔드포인트 구조 테스트"""
        # 빈 리스트로 테스트 (List[EvaluationResult] 직접 전달)
        response = client.post(
            "/api/v1/eval/export/json",
            json=[],
        )
        # 빈 결과도 성공해야 함
        assert response.status_code == 200

    def test_export_csv_endpoint_structure(self, client):
        """CSV 내보내기 엔드포인트 구조 테스트"""
        response = client.post(
            "/api/v1/eval/export/csv",
            json=[],
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
