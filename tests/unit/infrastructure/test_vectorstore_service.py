"""
VectorStoreService Unit Tests

Qdrant 벡터 저장소 서비스의 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestVectorStoreService:
    """VectorStoreService 테스트"""

    @pytest.fixture
    def mock_qdrant_client(self):
        """QdrantClient mock"""
        mock = MagicMock()
        mock.get_collections.return_value = MagicMock(collections=[])
        mock.get_collection.return_value = MagicMock(points_count=100)
        mock.query_points.return_value = MagicMock(points=[])
        mock.upsert.return_value = None
        mock.delete_collection.return_value = None
        mock.create_collection.return_value = None
        return mock

    @pytest.fixture
    def mock_embeddings(self):
        """OpenAIEmbeddings mock"""
        mock = MagicMock()
        # Return 3 vectors for 3 chunks
        mock.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
        mock.embed_query.return_value = [0.15] * 1536
        return mock

    @pytest.fixture
    def vectorstore_service(self, settings, mock_qdrant_client, mock_embeddings, mock_bm25_service):
        """VectorStoreService with mocks"""
        with patch('src.infrastructure.vectorstore_service.QdrantClient') as mock_client_class, \
             patch('src.infrastructure.vectorstore_service.OpenAIEmbeddings') as mock_emb_class:
            mock_client_class.return_value = mock_qdrant_client
            mock_emb_class.return_value = mock_embeddings

            from src.infrastructure.vectorstore_service import VectorStoreService
            service = VectorStoreService(settings)
            service._client = mock_qdrant_client
            service._embeddings = mock_embeddings
            service._bm25 = mock_bm25_service
            return service

    def test_is_ready_returns_true_when_connected(self, vectorstore_service, mock_qdrant_client):
        """Qdrant 연결 시 is_ready가 True 반환"""
        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])
        assert vectorstore_service.is_ready() is True

    def test_is_ready_returns_false_when_disconnected(self, vectorstore_service, mock_qdrant_client):
        """Qdrant 연결 실패 시 is_ready가 False 반환"""
        mock_qdrant_client.get_collections.side_effect = Exception("Connection failed")
        assert vectorstore_service.is_ready() is False

    def test_collection_exists_returns_true_when_exists(self, vectorstore_service, mock_qdrant_client, settings):
        """컬렉션 존재 시 True 반환"""
        mock_collection = MagicMock()
        mock_collection.name = settings.vectorstore.collection_name
        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[mock_collection])

        assert vectorstore_service.collection_exists() is True

    def test_collection_exists_returns_false_when_not_exists(self, vectorstore_service, mock_qdrant_client):
        """컬렉션 미존재 시 False 반환"""
        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])
        assert vectorstore_service.collection_exists() is False

    def test_add_chunks_returns_count(self, vectorstore_service, sample_chunks):
        """add_chunks가 저장된 청크 수 반환"""
        result = vectorstore_service.add_chunks(sample_chunks)
        assert result == len(sample_chunks)

    def test_add_chunks_empty_list_returns_zero(self, vectorstore_service):
        """빈 청크 목록 시 0 반환"""
        result = vectorstore_service.add_chunks([])
        assert result == 0

    def test_add_chunks_calls_upsert(self, vectorstore_service, mock_qdrant_client, sample_chunks):
        """add_chunks가 Qdrant upsert 호출"""
        vectorstore_service.add_chunks(sample_chunks)
        mock_qdrant_client.upsert.assert_called_once()

    def test_get_document_count_returns_count(self, vectorstore_service, mock_qdrant_client, settings):
        """get_document_count가 문서 수 반환"""
        mock_collection = MagicMock()
        mock_collection.name = settings.vectorstore.collection_name
        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[mock_collection])
        mock_qdrant_client.get_collection.return_value = MagicMock(points_count=150)

        result = vectorstore_service.get_document_count()
        assert result == 150

    def test_get_document_count_returns_zero_when_no_collection(self, vectorstore_service, mock_qdrant_client):
        """컬렉션 없을 시 0 반환"""
        mock_qdrant_client.get_collections.return_value = MagicMock(collections=[])

        result = vectorstore_service.get_document_count()
        assert result == 0

    def test_hybrid_search_returns_documents(self, vectorstore_service, mock_qdrant_client, mock_embeddings, mock_bm25_service):
        """hybrid_search가 문서 내용 목록 반환"""
        mock_point1 = MagicMock()
        mock_point1.payload = {"content": "Document 1"}
        mock_point2 = MagicMock()
        mock_point2.payload = {"content": "Document 2"}

        mock_qdrant_client.query_points.return_value = MagicMock(points=[mock_point1, mock_point2])

        with patch('src.infrastructure.vectorstore_service.Query') as mock_query, \
             patch('src.infrastructure.vectorstore_service.Prefetch') as mock_prefetch:
            mock_query.return_value = MagicMock()
            mock_prefetch.return_value = MagicMock()

            result = vectorstore_service.hybrid_search("test query")
            assert len(result) == 2
            assert result[0] == "Document 1"
            assert result[1] == "Document 2"

    def test_hybrid_search_calls_query_points(self, vectorstore_service, mock_qdrant_client, mock_embeddings, mock_bm25_service):
        """hybrid_search가 Qdrant query_points 호출"""
        mock_qdrant_client.query_points.return_value = MagicMock(points=[])

        with patch('src.infrastructure.vectorstore_service.Query') as mock_query, \
             patch('src.infrastructure.vectorstore_service.Prefetch') as mock_prefetch:
            mock_query.return_value = MagicMock()
            mock_prefetch.return_value = MagicMock()

            vectorstore_service.hybrid_search("test query")
            mock_qdrant_client.query_points.assert_called_once()

    def test_close_clears_client(self, vectorstore_service, mock_qdrant_client):
        """close가 클라이언트를 정리"""
        vectorstore_service.close()
        mock_qdrant_client.close.assert_called_once()
        assert vectorstore_service._client is None
