"""
Configuration settings for RAG Pipeline
"""
import os
from dataclasses import dataclass, field


@dataclass
class LLMSettings:
    """OpenAI API LLM Settings"""
    # QueryRewriteNode
    rewrite_model: str = "gpt-4o-mini"
    rewrite_temperature: float = 0.0

    # GeneratorNode
    generator_model: str = "gpt-4o"  # GPT-5 출시 시 변경 가능
    generator_temperature: float = 0.0


@dataclass
class EmbeddingSettings:
    """OpenAI Embedding Settings"""
    model: str = "text-embedding-3-small"
    dimensions: int = 1536  # text-embedding-3-small dimension


@dataclass
class VectorStoreSettings:
    """Qdrant VectorDB Settings (Hybrid Search: Dense + Sparse)"""
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    collection_name: str = "rag_chunks"
    dense_vector_name: str = "dense"
    sparse_vector_name: str = "bm25"
    dense_vector_size: int = 1536  # text-embedding-3-small


@dataclass
class RerankerSettings:
    """Infinity Reranker Server Settings"""
    base_url: str = "http://localhost:8002"
    model_name: str = "BAAI/bge-reranker-v2-m3"
    top_k: int = 5


@dataclass
class RetrieverSettings:
    """Retriever Settings"""
    initial_limit: int = 30


@dataclass
class PreprocessingSettings:
    """Preprocessing Settings"""
    max_pages: int = 3  # PDF 최대 처리 페이지 수 (0 = 무제한)
    embedding_model: str = "text-embedding-3-small"
    breakpoint_type: str = "percentile"
    breakpoint_threshold: float = 95.0
    min_chunk_size: int = 100
    max_chunk_size: int = 1500
    remove_extra_whitespace: bool = True
    remove_extra_newlines: bool = True
    remove_special_chars: bool = False
    min_line_length: int = 0


@dataclass
class RedisSettings:
    """Redis Cache Settings"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    ttl: int = 3600  # Cache TTL in seconds


@dataclass
class Settings:
    """전체 설정 관리"""
    llm: LLMSettings = field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = field(default_factory=EmbeddingSettings)
    vectorstore: VectorStoreSettings = field(default_factory=VectorStoreSettings)
    reranker: RerankerSettings = field(default_factory=RerankerSettings)
    retriever: RetrieverSettings = field(default_factory=RetrieverSettings)
    preprocessing: PreprocessingSettings = field(default_factory=PreprocessingSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)

    def __post_init__(self):
        # Qdrant 환경변수 오버라이드
        if os.getenv("QDRANT_HOST"):
            self.vectorstore.host = os.getenv("QDRANT_HOST")
        if os.getenv("QDRANT_PORT"):
            self.vectorstore.port = int(os.getenv("QDRANT_PORT"))
        if os.getenv("QDRANT_GRPC_PORT"):
            self.vectorstore.grpc_port = int(os.getenv("QDRANT_GRPC_PORT"))

        # Reranker 환경변수 오버라이드
        if os.getenv("RERANKER_BASE_URL"):
            self.reranker.base_url = os.getenv("RERANKER_BASE_URL")

        # Redis 환경변수 오버라이드
        if os.getenv("REDIS_HOST"):
            self.redis.host = os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            self.redis.port = int(os.getenv("REDIS_PORT"))


settings = Settings()
