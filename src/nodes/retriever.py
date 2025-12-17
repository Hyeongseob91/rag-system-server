"""Retriever Node"""
from typing import Dict, Any, List
from .base import BaseNode
from ..schemas import RAGState
from ..services import VectorStoreService, RerankerService


class RetrieverNode(BaseNode):
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

        for query in queries:
            print(f"    검색 쿼리: {query}")
            for content in self._vectorstore.hybrid_search(query):
                if content not in seen:
                    seen.add(content)
                    all_results.append(content)

        print(f"--- 1차 검색: {len(all_results)}개 ---")
        ranked = self._reranker.get_top_documents(state["question"], all_results)
        print(f"--- Reranking 후: {len(ranked)}개 ---")

        final_docs = []
        for idx, (doc, score) in enumerate(ranked):
            print(f"[{idx+1}등] Score: {score:.4f}")
            final_docs.append(doc)
        return {"retrieved_docs": final_docs}
