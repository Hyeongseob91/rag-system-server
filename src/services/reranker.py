"""
Reranker Service - Infinity API 기반
CrossEncoder 모델을 Infinity 서버에서 서빙
"""
from typing import List, Tuple, Optional

import httpx

from ..config import Settings


class RerankerService:
    """Infinity 서버 기반 Reranker 서비스

    Infinity API를 통해 Cross-Encoder 리랭킹을 수행합니다.
    GPU에서 서빙되는 모델을 API로 호출하여 사용합니다.

    Reference:
        https://github.com/michaelfeil/infinity
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.reranker.base_url
        self.top_k = settings.reranker.top_k
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """HTTP 클라이언트 (Lazy Loading)"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=60.0
            )
        return self._client

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """문서 리랭킹

        Args:
            query: 검색 쿼리
            documents: 리랭킹할 문서 리스트
            top_k: 반환할 상위 문서 수 (기본값: settings.reranker.top_k)

        Returns:
            (문서, 점수) 튜플 리스트 (점수 내림차순)
        """
        if not documents:
            return []

        if top_k is None:
            top_k = self.top_k

        # Infinity API 호출
        response = self.client.post(
            "/rerank",
            json={
                "query": query,
                "documents": documents,
                "return_documents": True
            }
        )
        response.raise_for_status()

        # 응답 파싱
        results = response.json().get("results", [])

        # (문서, 점수) 튜플 리스트로 변환
        ranked = [
            (r.get("document", {}).get("text", ""), r.get("relevance_score", 0.0))
            for r in results
        ]

        return ranked[:top_k]

    def get_top_documents(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """상위 문서 반환 (rerank의 별칭)"""
        return self.rerank(query, documents, top_k)

    def close(self):
        """HTTP 클라이언트 종료"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __del__(self):
        self.close()
