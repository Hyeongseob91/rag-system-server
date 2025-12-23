"""
Pytest Configuration and Fixtures

테스트에서 공통으로 사용하는 fixtures를 정의합니다.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from dataclasses import dataclass


# =============================================================================
# Settings Fixtures
# =============================================================================

@pytest.fixture
def settings():
    """기본 설정 fixture"""
    from src.core.config import Settings
    return Settings()


# =============================================================================
# Mock Service Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_service():
    """LLMService mock"""
    mock = MagicMock()
    mock.get_rewrite_llm.return_value = MagicMock()
    mock.get_generator_llm.return_value = MagicMock()
    mock.invoke_with_structured_output.return_value = MagicMock(datasource="vectorstore")
    mock.invoke_with_string_output.return_value = "Generated answer"
    return mock


@pytest.fixture
def mock_vectorstore_service():
    """VectorStoreService mock"""
    mock = MagicMock()
    mock.is_ready.return_value = True
    mock.collection_exists.return_value = True
    mock.get_document_count.return_value = 100
    mock.hybrid_search.return_value = ["doc1 content", "doc2 content", "doc3 content"]
    mock.add_chunks.return_value = 10
    return mock


@pytest.fixture
def mock_reranker_service():
    """RerankerService mock"""
    mock = MagicMock()
    mock.rerank.return_value = [
        {"document": "doc1 content", "relevance_score": 0.95},
        {"document": "doc2 content", "relevance_score": 0.85},
    ]
    mock.get_top_documents.return_value = ["doc1 content", "doc2 content"]
    return mock


@pytest.fixture
def mock_cache_service():
    """CacheService mock"""
    mock = MagicMock()
    mock.is_ready.return_value = True
    mock.get_cached_response.return_value = None
    mock.cache_response.return_value = True
    mock.invalidate_all.return_value = 5
    return mock


@pytest.fixture
def mock_bm25_service():
    """BM25Service mock"""
    mock = MagicMock()
    # SparseVector 형태로 반환 (3개 청크에 대해)
    sparse_vec = MagicMock(indices=[1, 2, 3], values=[0.5, 0.3, 0.2])
    mock.encode.return_value = [sparse_vec, sparse_vec, sparse_vec]
    mock.encode_query.return_value = MagicMock(indices=[1, 2], values=[0.6, 0.4])
    return mock


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@dataclass
class SampleChunk:
    """테스트용 청크 데이터"""
    content: str
    chunk_id: str = "test-chunk-id"
    chunk_index: int = 0
    doc_id: str = "test-doc-id"
    source: str = "/path/to/test.pdf"
    file_name: str = "test.pdf"
    file_type: str = "pdf"
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def char_count(self) -> int:
        return len(self.content)

    def to_qdrant_payload(self):
        from datetime import datetime
        return {
            "content": self.content,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "total_chunks": self.metadata.get("total_chunks", 1),
            "source": self.source,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "char_count": self.char_count,
            "page_number": self.metadata.get("page_number"),
            "sheet_name": self.metadata.get("sheet_name"),
            "created_at": datetime.now().isoformat(),
        }


@pytest.fixture
def sample_chunks():
    """샘플 청크 목록"""
    return [
        SampleChunk(content="This is the first chunk content.", chunk_id="chunk-1", chunk_index=0),
        SampleChunk(content="This is the second chunk content.", chunk_id="chunk-2", chunk_index=1),
        SampleChunk(content="This is the third chunk content.", chunk_id="chunk-3", chunk_index=2),
    ]


@pytest.fixture
def sample_question():
    """샘플 질문"""
    return "RAG 시스템의 동작 원리를 설명해주세요."


@pytest.fixture
def sample_documents():
    """샘플 검색 결과 문서"""
    return [
        "RAG는 Retrieval-Augmented Generation의 약자입니다.",
        "검색 기반 생성 모델은 외부 지식을 활용합니다.",
        "벡터 데이터베이스를 사용하여 관련 문서를 검색합니다.",
    ]


# =============================================================================
# State Fixtures
# =============================================================================

@pytest.fixture
def initial_rag_state(sample_question):
    """초기 RAGState"""
    return {
        "question": sample_question,
        "optimized_queries": [],
        "retrieved_docs": [],
        "final_answer": "",
    }


@pytest.fixture
def rag_state_after_rewrite(sample_question):
    """쿼리 리라이트 후 RAGState"""
    return {
        "question": sample_question,
        "optimized_queries": [
            "RAG 시스템 동작 원리",
            "Retrieval-Augmented Generation 설명",
            "검색 기반 생성 모델 작동 방식",
        ],
        "retrieved_docs": [],
        "final_answer": "",
    }


@pytest.fixture
def rag_state_after_retrieval(sample_question, sample_documents):
    """검색 후 RAGState"""
    return {
        "question": sample_question,
        "optimized_queries": [
            "RAG 시스템 동작 원리",
            "Retrieval-Augmented Generation 설명",
        ],
        "retrieved_docs": sample_documents,
        "final_answer": "",
    }


# =============================================================================
# API Test Fixtures
# =============================================================================

@pytest.fixture
def mock_rag_app(mock_llm_service, mock_vectorstore_service, mock_cache_service):
    """RAGApplication mock"""
    mock = MagicMock()
    mock.cache_service = mock_cache_service
    mock._workflow = MagicMock()
    mock._workflow.invoke.return_value = {
        "question": "test question",
        "optimized_queries": ["query1", "query2"],
        "retrieved_docs": ["doc1", "doc2"],
        "final_answer": "This is the generated answer.",
    }
    mock.conversation_repo = MagicMock()
    mock.document_repo = MagicMock()
    return mock
