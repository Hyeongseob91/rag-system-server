"""
Retrieval Metrics

검색 품질을 측정하는 메트릭 함수들

메트릭 설명:
- Recall@K: 상위 K개 문서 중 정답 문서가 포함된 비율
- nDCG@K: 순위를 고려한 관련성 점수 (높은 순위에 정답이 있을수록 좋음)
- MRR: 첫 번째 정답 문서의 역순위 평균
- Hit@K: 상위 K개 내에 정답이 하나라도 있는지 여부
"""

import math
from typing import List, Set, Optional
from src.evaluation.schemas import RetrievalMetrics


def recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Recall@K 계산

    상위 K개 검색 결과 중 정답 문서가 얼마나 포함되어 있는지 측정

    Args:
        retrieved_ids: 검색된 문서 ID 리스트 (순위순)
        relevant_ids: 정답 문서 ID 집합
        k: 상위 K개

    Returns:
        Recall@K 값 (0~1)

    Example:
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = {"doc1", "doc3", "doc6"}
        recall_at_k(retrieved, relevant, 5) = 2/3 = 0.667
    """
    if not relevant_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & relevant_ids)
    return hits / len(relevant_ids)


def ndcg_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Normalized Discounted Cumulative Gain (nDCG@K) 계산

    순위를 고려한 관련성 점수. 높은 순위에 정답이 있을수록 점수가 높음.

    Args:
        retrieved_ids: 검색된 문서 ID 리스트 (순위순)
        relevant_ids: 정답 문서 ID 집합
        k: 상위 K개

    Returns:
        nDCG@K 값 (0~1)

    공식:
        DCG = sum(rel_i / log2(i + 1)) for i in 1..k
        IDCG = 최적 순서일 때의 DCG
        nDCG = DCG / IDCG
    """
    if not relevant_ids:
        return 0.0

    # DCG 계산 (binary relevance: 정답이면 1, 아니면 0)
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in relevant_ids:
            # i+1은 순위 (1부터 시작)
            # log2(i+2)는 discount factor
            dcg += 1.0 / math.log2(i + 2)

    # IDCG 계산 (모든 정답이 최상위에 있을 때)
    num_relevant = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(num_relevant))

    if idcg == 0:
        return 0.0

    return dcg / idcg


def mrr(
    retrieved_ids: List[str],
    relevant_ids: Set[str]
) -> float:
    """
    Mean Reciprocal Rank (MRR) 계산

    첫 번째 정답 문서의 순위의 역수

    Args:
        retrieved_ids: 검색된 문서 ID 리스트 (순위순)
        relevant_ids: 정답 문서 ID 집합

    Returns:
        MRR 값 (0~1)

    Example:
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = {"doc3"}
        mrr = 1/3 = 0.333 (doc3가 3번째 위치)
    """
    if not relevant_ids:
        return 0.0

    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)

    return 0.0


def hit_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> bool:
    """
    Hit@K 계산

    상위 K개 내에 정답이 하나라도 있는지 여부

    Args:
        retrieved_ids: 검색된 문서 ID 리스트 (순위순)
        relevant_ids: 정답 문서 ID 집합
        k: 상위 K개

    Returns:
        True if hit, False otherwise
    """
    if not relevant_ids:
        return False

    top_k = set(retrieved_ids[:k])
    return len(top_k & relevant_ids) > 0


def precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int
) -> float:
    """
    Precision@K 계산

    상위 K개 중 정답 문서의 비율

    Args:
        retrieved_ids: 검색된 문서 ID 리스트 (순위순)
        relevant_ids: 정답 문서 ID 집합
        k: 상위 K개

    Returns:
        Precision@K 값 (0~1)
    """
    if k == 0:
        return 0.0

    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & relevant_ids)
    return hits / k


def calculate_retrieval_metrics(
    retrieved_doc_ids: List[str],
    relevant_doc_ids: Optional[List[str]] = None
) -> RetrievalMetrics:
    """
    모든 Retrieval 메트릭을 한 번에 계산

    Args:
        retrieved_doc_ids: 검색된 문서 ID 리스트 (순위순)
        relevant_doc_ids: 정답 문서 ID 리스트 (없으면 메트릭 0 반환)

    Returns:
        RetrievalMetrics 객체
    """
    # 정답이 없으면 기본값 반환
    if not relevant_doc_ids:
        return RetrievalMetrics(
            recall_at_5=0.0,
            recall_at_10=0.0,
            ndcg_at_10=0.0,
            mrr=0.0,
            hit_at_5=False,
            hit_at_10=False,
        )

    relevant_set = set(relevant_doc_ids)

    return RetrievalMetrics(
        recall_at_5=recall_at_k(retrieved_doc_ids, relevant_set, k=5),
        recall_at_10=recall_at_k(retrieved_doc_ids, relevant_set, k=10),
        ndcg_at_10=ndcg_at_k(retrieved_doc_ids, relevant_set, k=10),
        mrr=mrr(retrieved_doc_ids, relevant_set),
        hit_at_5=hit_at_k(retrieved_doc_ids, relevant_set, k=5),
        hit_at_10=hit_at_k(retrieved_doc_ids, relevant_set, k=10),
    )
