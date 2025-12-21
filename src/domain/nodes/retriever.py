"""
Retriever Node

Domain Layer: Hybrid Search + Reranking으로 관련 문서를 검색합니다.
"""
from typing import Dict, Any

from .base import BaseNode
from src.application.state import RAGState
from src.infrastructure import VectorStoreService, RerankerService


class RetrieverNode(BaseNode):
    """검색 노드

    2단계 검색 전략:
    1. Hybrid Search: Dense + Sparse로 후보 30개 검색
    2. Reranking: CrossEncoder로 상위 5개 재선정

    왜 2단계인가?
    - 1단계만: 빠르지만 정확도 낮음 (Bi-Encoder)
    - 2단계: 느리지만 정확도 높음 (Cross-Encoder)
    - 조합: 후보를 빠르게 찾고, 정밀하게 재정렬
    """

    def __init__(self, vectorstore_service: VectorStoreService, reranker_service: RerankerService):
        self._vectorstore = vectorstore_service
        self._reranker = reranker_service

    @property
    def name(self) -> str:
        return "retriever"

    def __call__(self, state: RAGState) -> Dict[str, Any]:
        print("--- [Step 2] Retriever 시작 ---")
        queries = state.get("optimized_queries", [state["question"]])
        all_results, seen = [], set()

        # 각 쿼리로 Hybrid Search
        for query in queries:
            print(f"    검색 쿼리: {query}")
            for content in self._vectorstore.hybrid_search(query):
                if content not in seen:
                    seen.add(content)
                    all_results.append(content)

        print(f"--- 1차 검색: {len(all_results)}개 ---")

        # Reranking
        ranked = self._reranker.get_top_documents(state["question"], all_results)
        print(f"--- Reranking 후: {len(ranked)}개 ---")

        final_docs = []
        for idx, (doc, score) in enumerate(ranked):
            print(f"[{idx+1}등] Score: {score:.4f}")
            final_docs.append(doc)

        return {"retrieved_docs": final_docs}
