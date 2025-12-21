"""
BM25 Sparse Vector Service - FastEmbed 기반
Qdrant Hybrid Search를 위한 BM25 Sparse Vector 생성
"""
from typing import List

from fastembed import SparseTextEmbedding
from qdrant_client.models import SparseVector


class BM25Service:
    """FastEmbed 기반 BM25 Sparse Vector 서비스

    Qdrant Hybrid Search에서 Dense Vector와 함께 사용되는
    BM25 기반 Sparse Vector를 생성합니다.

    Reference:
        https://qdrant.tech/articles/hybrid-search/
        https://github.com/qdrant/fastembed
    """

    def __init__(self, model_name: str = "Qdrant/bm25"):
        """
        Args:
            model_name: FastEmbed BM25 모델명 (기본값: "Qdrant/bm25")
        """
        self._model = SparseTextEmbedding(model_name)

    def encode(self, texts: List[str]) -> List[SparseVector]:
        """텍스트 리스트를 BM25 sparse vector로 변환

        Args:
            texts: 변환할 텍스트 리스트

        Returns:
            SparseVector 리스트 (indices, values)
        """
        if not texts:
            return []

        embeddings = list(self._model.embed(texts))
        return [
            SparseVector(
                indices=emb.indices.tolist(),
                values=emb.values.tolist()
            )
            for emb in embeddings
        ]

    def encode_query(self, query: str) -> SparseVector:
        """단일 쿼리를 BM25 sparse vector로 변환

        Args:
            query: 변환할 쿼리 텍스트

        Returns:
            SparseVector (indices, values)
        """
        embeddings = self.encode([query])
        return embeddings[0] if embeddings else SparseVector(indices=[], values=[])

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[SparseVector]:
        """대량의 텍스트를 배치로 변환

        Args:
            texts: 변환할 텍스트 리스트
            batch_size: 배치 크기 (기본값: 32)

        Returns:
            SparseVector 리스트
        """
        all_vectors = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            vectors = self.encode(batch)
            all_vectors.extend(vectors)
        return all_vectors
