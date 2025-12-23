"""
BM25Service Unit Tests

BM25 Sparse Vector 서비스의 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestBM25Service:
    """BM25Service 테스트"""

    @pytest.fixture
    def mock_sparse_embedding(self):
        """SparseTextEmbedding mock"""
        mock = MagicMock()
        # SparseEmbedding 형태 반환 (fastembed 형식)
        sparse_result = MagicMock()
        sparse_result.indices = np.array([1, 5, 10])
        sparse_result.values = np.array([0.5, 0.3, 0.2])
        mock.embed.return_value = iter([sparse_result, sparse_result])
        return mock

    @pytest.fixture
    def bm25_service(self, mock_sparse_embedding):
        """BM25Service with mocked SparseTextEmbedding"""
        with patch('src.infrastructure.bm25_service.SparseTextEmbedding') as mock_class:
            mock_class.return_value = mock_sparse_embedding
            from src.infrastructure.bm25_service import BM25Service
            service = BM25Service()
            return service

    def test_encode_returns_sparse_vectors(self, bm25_service, mock_sparse_embedding):
        """encode가 Sparse 벡터 목록 반환"""
        texts = ["First document", "Second document"]
        result = bm25_service.encode(texts)

        assert len(result) == 2
        mock_sparse_embedding.embed.assert_called_once_with(texts)

    def test_encode_query_returns_sparse_vector(self, bm25_service):
        """encode_query가 단일 Sparse 벡터 반환"""
        query = "test query"
        result = bm25_service.encode_query(query)

        assert result is not None

    def test_encode_empty_list_returns_empty(self, bm25_service):
        """빈 리스트 입력 시 빈 리스트 반환"""
        result = bm25_service.encode([])
        assert result == []

    def test_sparse_vector_has_indices_and_values(self, bm25_service):
        """Sparse 벡터가 indices와 values 포함"""
        result = bm25_service.encode_query("test query")

        assert hasattr(result, 'indices')
        assert hasattr(result, 'values')

    def test_encode_batch_processes_in_batches(self, bm25_service, mock_sparse_embedding):
        """encode_batch가 배치 단위로 처리"""
        texts = ["doc"] * 100
        result = bm25_service.encode_batch(texts, batch_size=32)

        # 100개 텍스트, 32배치 = 4번 호출 (32, 32, 32, 4)
        assert mock_sparse_embedding.embed.call_count == 4
