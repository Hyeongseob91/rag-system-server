"""
Experiment Profiles

RAG 파이프라인의 다양한 설정 조합을 정의하는 실험 프로파일

사용 목적:
- A/B 테스트: 다른 설정으로 동일 질문 평가
- Ablation Study: 특정 기능(Reranker 등) 제거 시 성능 변화 측정
- 포트폴리오: "hybrid_rerank vs baseline" 비교 결과 시각화
"""

from dataclasses import dataclass, field
from typing import Dict, Literal


@dataclass
class ExperimentProfile:
    """실험 프로파일 정의"""

    # 식별자
    id: str
    name: str
    description: str = ""

    # Retrieval 설정
    retriever_type: Literal["dense", "sparse", "hybrid"] = "hybrid"
    initial_retrieval_limit: int = 30  # 1차 검색 후보 수

    # Reranking 설정
    use_reranker: bool = True
    rerank_top_k: int = 5  # Reranking 후 반환할 문서 수

    # Query Rewriting 설정
    use_query_rewrite: bool = True
    num_rewrite_queries: int = 5  # 생성할 쿼리 변형 수

    # LLM 설정
    generator_model: str = "gpt-4o"
    generator_temperature: float = 0.0

    def __post_init__(self):
        """유효성 검사"""
        if self.rerank_top_k > self.initial_retrieval_limit:
            raise ValueError(
                f"rerank_top_k ({self.rerank_top_k}) cannot exceed "
                f"initial_retrieval_limit ({self.initial_retrieval_limit})"
            )


# 사전 정의된 프로파일들
PROFILES: Dict[str, ExperimentProfile] = {
    # Baseline: Dense Search만 사용, Reranker/Query Rewrite 없음
    "baseline": ExperimentProfile(
        id="baseline",
        name="Baseline (Dense Only)",
        description="Dense embedding만 사용. Reranker와 Query Rewrite 미적용.",
        retriever_type="dense",
        initial_retrieval_limit=10,
        use_reranker=False,
        rerank_top_k=10,
        use_query_rewrite=False,
        num_rewrite_queries=1,
    ),

    # Hybrid: Dense + Sparse, Reranker 없음
    "hybrid_v1": ExperimentProfile(
        id="hybrid_v1",
        name="Hybrid Search",
        description="Dense + BM25 Hybrid Search. Reranker 미적용.",
        retriever_type="hybrid",
        initial_retrieval_limit=10,
        use_reranker=False,
        rerank_top_k=10,
        use_query_rewrite=False,
        num_rewrite_queries=1,
    ),

    # Hybrid + Query Rewrite
    "hybrid_rewrite": ExperimentProfile(
        id="hybrid_rewrite",
        name="Hybrid + Query Rewrite",
        description="Hybrid Search + 쿼리 확장. Reranker 미적용.",
        retriever_type="hybrid",
        initial_retrieval_limit=20,
        use_reranker=False,
        rerank_top_k=10,
        use_query_rewrite=True,
        num_rewrite_queries=5,
    ),

    # Full Pipeline: 모든 기능 활성화 (현재 기본값)
    "hybrid_rerank": ExperimentProfile(
        id="hybrid_rerank",
        name="Full Pipeline (Hybrid + Rerank)",
        description="Hybrid Search + Query Rewrite + Cross-Encoder Reranking. 최고 품질.",
        retriever_type="hybrid",
        initial_retrieval_limit=30,
        use_reranker=True,
        rerank_top_k=5,
        use_query_rewrite=True,
        num_rewrite_queries=5,
    ),

    # Fast: 빠른 응답 우선 (정확도 희생)
    "fast": ExperimentProfile(
        id="fast",
        name="Fast Mode",
        description="빠른 응답 우선. Reranker 미적용, 적은 후보.",
        retriever_type="hybrid",
        initial_retrieval_limit=10,
        use_reranker=False,
        rerank_top_k=5,
        use_query_rewrite=False,
        num_rewrite_queries=1,
        generator_model="gpt-4o-mini",
    ),
}


def get_profile(profile_id: str) -> ExperimentProfile:
    """
    프로파일 ID로 프로파일 조회

    Args:
        profile_id: 프로파일 ID

    Returns:
        ExperimentProfile 객체

    Raises:
        ValueError: 존재하지 않는 프로파일 ID
    """
    if profile_id not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise ValueError(
            f"Unknown profile: '{profile_id}'. Available profiles: {available}"
        )
    return PROFILES[profile_id]


def list_profiles() -> Dict[str, ExperimentProfile]:
    """
    모든 프로파일 목록 반환

    Returns:
        프로파일 ID → ExperimentProfile 딕셔너리
    """
    return PROFILES.copy()


def get_profile_summary(profile_id: str) -> dict:
    """
    프로파일 요약 정보 반환 (API 응답용)

    Args:
        profile_id: 프로파일 ID

    Returns:
        프로파일 요약 딕셔너리
    """
    profile = get_profile(profile_id)
    return {
        "id": profile.id,
        "name": profile.name,
        "description": profile.description,
        "retriever_type": profile.retriever_type,
        "use_reranker": profile.use_reranker,
        "use_query_rewrite": profile.use_query_rewrite,
    }


def list_profile_summaries() -> list:
    """
    모든 프로파일 요약 목록 반환 (API 응답용)

    Returns:
        프로파일 요약 리스트
    """
    return [get_profile_summary(pid) for pid in PROFILES]
