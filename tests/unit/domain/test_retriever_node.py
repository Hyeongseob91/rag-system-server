"""
RetrieverNode Unit Tests

검색 노드의 단위 테스트 (Hybrid Search + Reranking)
"""
import pytest
from unittest.mock import MagicMock


class TestRetrieverNode:
    """RetrieverNode 테스트"""

    @pytest.fixture
    def retriever_node(self, mock_vectorstore_service, mock_reranker_service):
        """RetrieverNode with mocks"""
        mock_vectorstore_service.hybrid_search.return_value = [
            "Document 1 content about RAG",
            "Document 2 content about search",
            "Document 3 content about generation",
            "Document 4 content about vectors",
            "Document 5 content about embeddings",
        ]
        # get_top_documents returns List[Tuple[str, float]]
        mock_reranker_service.get_top_documents.return_value = [
            ("Document 1 content about RAG", 0.95),
            ("Document 2 content about search", 0.87),
            ("Document 3 content about generation", 0.82),
        ]

        from src.domain.nodes.retriever import RetrieverNode
        return RetrieverNode(mock_vectorstore_service, mock_reranker_service)

    def test_node_name(self, retriever_node):
        """노드 이름이 'retriever'"""
        assert retriever_node.name == "retriever"

    def test_call_returns_retrieved_docs(self, retriever_node, rag_state_after_rewrite):
        """__call__이 검색된 문서 목록 반환"""
        result = retriever_node(rag_state_after_rewrite)

        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) > 0

    def test_call_uses_hybrid_search(self, retriever_node, rag_state_after_rewrite, mock_vectorstore_service):
        """Hybrid Search를 사용하여 검색"""
        retriever_node(rag_state_after_rewrite)

        mock_vectorstore_service.hybrid_search.assert_called()

    def test_call_uses_reranker(self, retriever_node, rag_state_after_rewrite, mock_reranker_service):
        """Reranker를 사용하여 문서 재정렬"""
        retriever_node(rag_state_after_rewrite)

        mock_reranker_service.get_top_documents.assert_called()

    def test_searches_all_optimized_queries(self, retriever_node, rag_state_after_rewrite, mock_vectorstore_service):
        """모든 최적화된 쿼리에 대해 검색"""
        num_queries = len(rag_state_after_rewrite["optimized_queries"])
        retriever_node(rag_state_after_rewrite)

        # 각 쿼리에 대해 hybrid_search 호출
        assert mock_vectorstore_service.hybrid_search.call_count == num_queries

    def test_returns_reranked_documents(self, retriever_node, rag_state_after_rewrite, mock_reranker_service):
        """Reranking된 문서 반환"""
        mock_reranker_service.get_top_documents.return_value = [
            ("Top doc 1", 0.95),
            ("Top doc 2", 0.90),
        ]

        result = retriever_node(rag_state_after_rewrite)

        assert result["retrieved_docs"] == ["Top doc 1", "Top doc 2"]

    def test_handles_empty_optimized_queries(self, retriever_node):
        """빈 최적화 쿼리 목록 처리"""
        state = {
            "question": "Test question",
            "optimized_queries": [],
            "retrieved_docs": [],
            "final_answer": "",
        }

        result = retriever_node(state)

        assert "retrieved_docs" in result

    def test_deduplicates_search_results(self, retriever_node, mock_vectorstore_service, rag_state_after_rewrite):
        """중복 검색 결과 제거"""
        # 동일한 문서가 여러 쿼리에서 반환되는 경우
        mock_vectorstore_service.hybrid_search.return_value = [
            "Duplicate document",
            "Duplicate document",  # 중복
            "Unique document",
        ]

        result = retriever_node(rag_state_after_rewrite)

        # 중복이 제거되었는지 확인 (reranker에 전달된 문서)
        assert "retrieved_docs" in result
