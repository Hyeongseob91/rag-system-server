"""
CacheService Unit Tests

Redis 캐시 서비스의 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch


class TestCacheService:
    """CacheService 테스트"""

    @pytest.fixture
    def mock_redis(self):
        """Redis 클라이언트 mock"""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.set.return_value = True
        mock.setex.return_value = True
        mock.keys.return_value = []
        mock.delete.return_value = 0
        return mock

    @pytest.fixture
    def cache_service(self, settings, mock_redis):
        """CacheService with mocked Redis"""
        with patch('src.infrastructure.cache_service.redis.Redis') as mock_redis_class:
            mock_redis_class.return_value = mock_redis
            from src.infrastructure.cache_service import CacheService
            service = CacheService(settings)
            service._client = mock_redis
            return service

    def test_is_ready_returns_true_when_connected(self, cache_service, mock_redis):
        """Redis 연결 시 is_ready가 True 반환"""
        mock_redis.ping.return_value = True
        assert cache_service.is_ready() is True

    def test_is_ready_returns_false_when_disconnected(self, cache_service, mock_redis):
        """Redis 연결 실패 시 is_ready가 False 반환"""
        import redis
        mock_redis.ping.side_effect = redis.RedisError("Connection failed")
        assert cache_service.is_ready() is False

    def test_get_cached_response_returns_none_when_miss(self, cache_service, mock_redis):
        """캐시 미스 시 None 반환"""
        mock_redis.get.return_value = None
        result = cache_service.get_cached_response("test question")
        assert result is None

    def test_get_cached_response_returns_data_when_hit(self, cache_service, mock_redis):
        """캐시 히트 시 데이터 반환"""
        import json
        cached_data = {
            "answer": "Cached answer",
            "sources": [],
            "processing_time_ms": 100.0,
            "cached": True
        }
        # decode_responses=True이므로 문자열로 반환
        mock_redis.get.return_value = json.dumps(cached_data)

        result = cache_service.get_cached_response("test question")
        assert result is not None
        assert result["answer"] == "Cached answer"

    def test_cache_response_stores_data(self, cache_service, mock_redis):
        """응답 캐싱이 Redis에 데이터 저장"""
        cache_service.cache_response(
            question="test question",
            answer="test answer",
            sources=[],
            processing_time_ms=150.0
        )
        # 실제 코드는 setex 사용 (TTL 포함)
        mock_redis.setex.assert_called_once()

    def test_invalidate_all_deletes_rag_keys(self, cache_service, mock_redis):
        """invalidate_all이 RAG 캐시 키를 삭제"""
        mock_redis.keys.return_value = [b"rag:query:abc", b"rag:query:def"]
        mock_redis.delete.return_value = 2

        result = cache_service.invalidate_all()
        assert result == 2
        mock_redis.delete.assert_called_once()

    def test_invalidate_all_returns_zero_when_no_keys(self, cache_service, mock_redis):
        """삭제할 키가 없으면 0 반환"""
        mock_redis.keys.return_value = []

        result = cache_service.invalidate_all()
        assert result == 0

    def test_make_key_generates_consistent_hash(self, cache_service):
        """동일한 질문에 대해 일관된 키 생성"""
        key1 = cache_service._make_key("test question")
        key2 = cache_service._make_key("test question")
        key3 = cache_service._make_key("different question")

        assert key1 == key2
        assert key1 != key3
        assert key1.startswith("rag:query:")

    def test_make_key_normalizes_input(self, cache_service):
        """질문 정규화 (공백 제거, 소문자)"""
        key1 = cache_service._make_key("Test Question")
        key2 = cache_service._make_key("  test question  ")
        key3 = cache_service._make_key("TEST QUESTION")

        assert key1 == key2 == key3
