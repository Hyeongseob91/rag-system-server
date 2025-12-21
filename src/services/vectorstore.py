"""
VectorStore Service - Qdrant Hybrid Search (Dense + BM25 Sparse)
"""
import uuid
from typing import TYPE_CHECKING, List, Optional

from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Prefetch,
    Query,
    SparseVectorParams,
    VectorParams,
)

from ..config import Settings
from .bm25 import BM25Service

if TYPE_CHECKING:
    from ..schemas.preprocessing import Chunk


class VectorStoreService:
    """Qdrant Hybrid Search (Dense + BM25 Sparse) 서비스

    Dense Vector (OpenAI Embeddings)와 Sparse Vector (BM25)를 함께 사용하여
    Hybrid Search를 수행합니다. RRF (Reciprocal Rank Fusion)로 결과를 융합합니다.

    Reference:
        https://qdrant.tech/articles/hybrid-search/
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[QdrantClient] = None
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._bm25: Optional[BM25Service] = None

    @property
    def client(self) -> QdrantClient:
        """Qdrant 클라이언트 (Lazy Loading)"""
        if self._client is None:
            self._client = QdrantClient(
                host=self.settings.vectorstore.host,
                port=self.settings.vectorstore.port,
            )
        return self._client

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        """OpenAI Embeddings (Lazy Loading)"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=self.settings.embedding.model
            )
        return self._embeddings

    @property
    def bm25(self) -> BM25Service:
        """BM25 Service (Lazy Loading)"""
        if self._bm25 is None:
            self._bm25 = BM25Service()
        return self._bm25

    def is_ready(self) -> bool:
        """Qdrant 서버 연결 확인"""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """클라이언트 종료"""
        if self._client is not None:
            self._client.close()
            self._client = None

    def collection_exists(self) -> bool:
        """컬렉션 존재 여부 확인"""
        collections = self.client.get_collections().collections
        return any(c.name == self.settings.vectorstore.collection_name for c in collections)

    def create_collection(self) -> None:
        """컬렉션 생성 (Dense + Sparse 벡터)"""
        collection_name = self.settings.vectorstore.collection_name

        # 기존 컬렉션 삭제
        if self.collection_exists():
            self.client.delete_collection(collection_name)

        # 새 컬렉션 생성 (Dense + Sparse)
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config={
                self.settings.vectorstore.dense_vector_name: VectorParams(
                    size=self.settings.vectorstore.dense_vector_size,
                    distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                self.settings.vectorstore.sparse_vector_name: SparseVectorParams()
            }
        )

    def add_chunks(self, chunks: List["Chunk"]) -> int:
        """청크 추가 (Dense + Sparse 벡터 동시 저장)

        Args:
            chunks: 저장할 청크 리스트

        Returns:
            추가된 청크 수
        """
        if not chunks:
            return 0

        texts = [c.content for c in chunks]

        # Dense vectors (OpenAI)
        dense_vectors = self.embeddings.embed_documents(texts)

        # Sparse vectors (BM25)
        sparse_vectors = self.bm25.encode(texts)

        # Points 생성
        points = []
        for i, (chunk, dense_vec, sparse_vec) in enumerate(zip(chunks, dense_vectors, sparse_vectors)):
            point_id = str(uuid.uuid4())
            payload = chunk.to_qdrant_payload()

            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        self.settings.vectorstore.dense_vector_name: dense_vec,
                        self.settings.vectorstore.sparse_vector_name: sparse_vec
                    },
                    payload=payload
                )
            )

        # Qdrant에 저장
        self.client.upsert(
            collection_name=self.settings.vectorstore.collection_name,
            points=points
        )

        return len(points)

    def get_document_count(self) -> int:
        """저장된 문서(청크) 수 조회"""
        if not self.collection_exists():
            return 0
        collection_info = self.client.get_collection(self.settings.vectorstore.collection_name)
        return collection_info.points_count or 0

    def hybrid_search(self, query: str, limit: Optional[int] = None) -> List[str]:
        """Hybrid Search (Dense + BM25) with RRF Fusion

        Args:
            query: 검색 쿼리
            limit: 반환할 결과 수 (기본값: settings.retriever.initial_limit)

        Returns:
            검색된 문서 내용 리스트
        """
        if limit is None:
            limit = self.settings.retriever.initial_limit

        # 쿼리 벡터 생성
        dense_query = self.embeddings.embed_query(query)
        sparse_query = self.bm25.encode_query(query)

        # Hybrid Search with Prefetch + RRF
        results = self.client.query_points(
            collection_name=self.settings.vectorstore.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_query,
                    using=self.settings.vectorstore.dense_vector_name,
                    limit=limit
                ),
                Prefetch(
                    query=sparse_query,
                    using=self.settings.vectorstore.sparse_vector_name,
                    limit=limit
                )
            ],
            query=Query(fusion="rrf"),  # Reciprocal Rank Fusion
            limit=limit
        )

        return [point.payload.get("content", "") for point in results.points]

    def search_by_file(self, file_name: str, limit: int = 100) -> List[str]:
        """특정 파일에서 검색

        Args:
            file_name: 파일명
            limit: 반환할 결과 수

        Returns:
            해당 파일의 문서 내용 리스트
        """
        results = self.client.scroll(
            collection_name=self.settings.vectorstore.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="file_name",
                        match=MatchValue(value=file_name)
                    )
                ]
            ),
            limit=limit
        )

        return [point.payload.get("content", "") for point in results[0]]

    def delete_by_file(self, file_name: str) -> int:
        """특정 파일의 모든 청크 삭제

        Args:
            file_name: 삭제할 파일명

        Returns:
            삭제된 청크 수
        """
        # 삭제 전 개수 확인
        before_count = len(self.search_by_file(file_name))

        # 삭제
        self.client.delete(
            collection_name=self.settings.vectorstore.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_name",
                        match=MatchValue(value=file_name)
                    )
                ]
            )
        )

        return before_count
