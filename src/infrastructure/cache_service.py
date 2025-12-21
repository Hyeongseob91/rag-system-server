"""
Redis Cache Service

Infrastructure Layer: 캐시 관리 (쿼리-응답 캐싱)
"""
import json
import hashlib
from typing import Optional, Any

import redis

from src.core import Settings


class CacheService:
    """Redis 기반 캐시 서비스"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Lazy Loading 패턴"""
        if self._client is None:
            self._client = redis.Redis(
                host=self.settings.redis.host,
                port=self.settings.redis.port,
                db=self.settings.redis.db,
                decode_responses=True
            )
        return self._client

    def _make_key(self, question: str) -> str:
        """질문을 해시하여 캐시 키 생성"""
        normalized = question.strip().lower()
        hash_value = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"rag:query:{hash_value}"

    def get_cached_response(self, question: str) -> Optional[dict]:
        """캐시된 응답 조회

        Args:
            question: 사용자 질문

        Returns:
            캐시된 응답 dict 또는 None
        """
        try:
            key = self._make_key(question)
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except redis.RedisError:
            # Redis 연결 실패 시 캐시 미스로 처리
            return None

    def cache_response(
        self,
        question: str,
        answer: str,
        sources: list,
        processing_time_ms: float
    ) -> bool:
        """응답을 캐시에 저장

        Args:
            question: 사용자 질문
            answer: 생성된 답변
            sources: 출처 목록
            processing_time_ms: 처리 시간

        Returns:
            저장 성공 여부
        """
        try:
            key = self._make_key(question)
            data = {
                "answer": answer,
                "sources": sources,
                "processing_time_ms": processing_time_ms,
                "cached": True
            }
            self.client.setex(
                key,
                self.settings.redis.ttl,
                json.dumps(data, ensure_ascii=False)
            )
            return True
        except redis.RedisError:
            return False

    def invalidate_all(self) -> int:
        """모든 RAG 쿼리 캐시 삭제 (문서 업로드 시 호출)

        Returns:
            삭제된 키 개수
        """
        try:
            keys = self.client.keys("rag:query:*")
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0

    def is_ready(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False

    def close(self) -> None:
        """Redis 연결 종료"""
        if self._client is not None:
            self._client.close()
            self._client = None
