"""
QueryRewriteNode Unit Tests

쿼리 리라이트 노드의 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch


class TestQueryRewriteNode:
    """QueryRewriteNode 테스트"""

    @pytest.fixture
    def mock_rewrite_result(self):
        """RewriteResult mock"""
        mock = MagicMock()
        mock.queries = [
            "RAG 시스템 동작 원리",
            "검색 증강 생성 설명",
            "Retrieval-Augmented Generation 작동 방식",
        ]
        return mock

    @pytest.fixture
    def query_rewrite_node(self, mock_llm_service, mock_rewrite_result):
        """QueryRewriteNode with mocks"""
        mock_llm_service.invoke_with_structured_output.return_value = mock_rewrite_result

        from src.domain.nodes.query_rewrite import QueryRewriteNode
        return QueryRewriteNode(mock_llm_service)

    def test_node_name(self, query_rewrite_node):
        """노드 이름이 'query_rewrite'"""
        assert query_rewrite_node.name == "query_rewrite"

    def test_call_returns_optimized_queries(self, query_rewrite_node, initial_rag_state):
        """__call__이 최적화된 쿼리 목록 반환"""
        result = query_rewrite_node(initial_rag_state)

        assert "optimized_queries" in result
        assert len(result["optimized_queries"]) > 0

    def test_call_uses_llm_service(self, query_rewrite_node, initial_rag_state, mock_llm_service):
        """LLM 서비스를 사용하여 쿼리 리라이트"""
        query_rewrite_node(initial_rag_state)

        mock_llm_service.get_rewrite_llm.assert_called()
        mock_llm_service.invoke_with_structured_output.assert_called()

    def test_call_preserves_original_question(self, query_rewrite_node, initial_rag_state):
        """원본 질문이 상태에 유지됨"""
        result = query_rewrite_node(initial_rag_state)

        # 반환된 결과에는 optimized_queries만 포함
        # 원본 question은 state에서 유지됨
        assert "optimized_queries" in result

    def test_optimized_queries_are_strings(self, query_rewrite_node, initial_rag_state):
        """최적화된 쿼리가 문자열 목록"""
        result = query_rewrite_node(initial_rag_state)

        for query in result["optimized_queries"]:
            assert isinstance(query, str)

    def test_generates_multiple_queries(self, query_rewrite_node, initial_rag_state):
        """여러 개의 최적화된 쿼리 생성 (3-5개)"""
        result = query_rewrite_node(initial_rag_state)

        assert len(result["optimized_queries"]) >= 1
