"""
GeneratorNode Unit Tests

답변 생성 노드의 단위 테스트
"""
import pytest
from unittest.mock import MagicMock


class TestGeneratorNode:
    """GeneratorNode 테스트"""

    @pytest.fixture
    def generator_node(self, mock_llm_service):
        """GeneratorNode with mocks"""
        mock_llm_service.invoke_with_string_output.return_value = (
            "RAG(Retrieval-Augmented Generation)는 검색 기반 생성 모델입니다. "
            "[1] 벡터 데이터베이스를 사용하여 관련 문서를 검색하고, "
            "[2] LLM을 통해 답변을 생성합니다."
        )

        from src.domain.nodes.generator import GeneratorNode
        return GeneratorNode(mock_llm_service)

    def test_node_name(self, generator_node):
        """노드 이름이 'generator'"""
        assert generator_node.name == "generator"

    def test_call_returns_final_answer(self, generator_node, rag_state_after_retrieval):
        """__call__이 최종 답변 반환"""
        result = generator_node(rag_state_after_retrieval)

        assert "final_answer" in result
        assert len(result["final_answer"]) > 0

    def test_call_uses_llm_service(self, generator_node, rag_state_after_retrieval, mock_llm_service):
        """LLM 서비스를 사용하여 답변 생성"""
        generator_node(rag_state_after_retrieval)

        mock_llm_service.get_generator_llm.assert_called()
        mock_llm_service.invoke_with_string_output.assert_called()

    def test_answer_contains_content(self, generator_node, rag_state_after_retrieval):
        """생성된 답변에 내용 포함"""
        result = generator_node(rag_state_after_retrieval)

        answer = result["final_answer"]
        assert isinstance(answer, str)
        assert len(answer) > 10

    def test_handles_empty_retrieved_docs(self, generator_node, mock_llm_service):
        """검색 결과가 없을 때 처리"""
        mock_llm_service.invoke_with_string_output.return_value = (
            "제공된 문서에서 해당 정보를 찾을 수 없습니다."
        )

        state = {
            "question": "Test question",
            "optimized_queries": [],
            "retrieved_docs": [],
            "final_answer": "",
        }

        result = generator_node(state)

        assert "final_answer" in result
        assert len(result["final_answer"]) > 0


class TestSimpleGeneratorNode:
    """SimpleGeneratorNode 테스트 (일반 대화 경로)"""

    @pytest.fixture
    def simple_generator_node(self, mock_llm_service):
        """SimpleGeneratorNode with mocks"""
        mock_llm_service.invoke_with_string_output.return_value = (
            "안녕하세요! 무엇을 도와드릴까요?"
        )

        from src.domain.nodes.simple_generator import SimpleGeneratorNode
        return SimpleGeneratorNode(mock_llm_service)

    def test_node_name(self, simple_generator_node):
        """노드 이름이 'simple_generator'"""
        assert simple_generator_node.name == "simple_generator"

    def test_call_returns_final_answer(self, simple_generator_node, initial_rag_state):
        """__call__이 최종 답변 반환"""
        result = simple_generator_node(initial_rag_state)

        assert "final_answer" in result
        assert len(result["final_answer"]) > 0

    def test_call_uses_llm_directly(self, simple_generator_node, initial_rag_state, mock_llm_service):
        """검색 없이 LLM 직접 사용"""
        simple_generator_node(initial_rag_state)

        mock_llm_service.get_generator_llm.assert_called()
        mock_llm_service.invoke_with_string_output.assert_called()

    def test_handles_greeting(self, simple_generator_node, mock_llm_service):
        """인사 처리"""
        mock_llm_service.invoke_with_string_output.return_value = "안녕하세요!"

        state = {
            "question": "안녕하세요",
            "optimized_queries": [],
            "retrieved_docs": [],
            "final_answer": "",
        }

        result = simple_generator_node(state)

        assert "안녕" in result["final_answer"]

    def test_no_sources_in_response(self, simple_generator_node, initial_rag_state):
        """일반 대화는 출처 없음"""
        result = simple_generator_node(initial_rag_state)

        # retrieved_docs는 변경되지 않음
        assert "retrieved_docs" not in result or result.get("retrieved_docs") == []
