"""
Configuration settings for RAG Pipeline

Cross-cutting concern: 모든 레이어에서 사용하는 설정값
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
    generator_model: str = "gpt-4o"
    generator_temperature: float = 0.0


@dataclass
class EmbeddingSettings:
    """OpenAI Embedding Settings"""
    model: str = "text-embedding-3-small"
    dimensions: int = 1536


@dataclass
class VectorStoreSettings:
    """Qdrant VectorDB Settings (Hybrid Search: Dense + Sparse)"""
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    collection_name: str = "rag_chunks"
    dense_vector_name: str = "dense"
    sparse_vector_name: str = "bm25"
    dense_vector_size: int = 1536


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
    max_pages: int = 3
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
    ttl: int = 3600  # 캐시 TTL (초)


@dataclass
class DatabaseSettings:
    """PostgreSQL Database Settings"""
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "password"
    database: str = "rag_db"

    @property
    def url(self) -> str:
        """SQLAlchemy 연결 URL"""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class JWTSettings:
    """JWT Authentication Settings"""
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    expire_minutes: int = 60 * 24  # 24시간


@dataclass
class Settings:
    """전체 설정 관리 (Cross-Cutting Concern)"""
    llm: LLMSettings = field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = field(default_factory=EmbeddingSettings)
    vectorstore: VectorStoreSettings = field(default_factory=VectorStoreSettings)
    reranker: RerankerSettings = field(default_factory=RerankerSettings)
    retriever: RetrieverSettings = field(default_factory=RetrieverSettings)
    preprocessing: PreprocessingSettings = field(default_factory=PreprocessingSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    jwt: JWTSettings = field(default_factory=JWTSettings)

    def __post_init__(self):
        # 환경변수 오버라이드 - Qdrant
        if os.getenv("QDRANT_HOST"):
            self.vectorstore.host = os.getenv("QDRANT_HOST")
        if os.getenv("QDRANT_PORT"):
            self.vectorstore.port = int(os.getenv("QDRANT_PORT"))
        if os.getenv("QDRANT_GRPC_PORT"):
            self.vectorstore.grpc_port = int(os.getenv("QDRANT_GRPC_PORT"))

        # 환경변수 오버라이드 - Reranker
        if os.getenv("RERANKER_BASE_URL"):
            self.reranker.base_url = os.getenv("RERANKER_BASE_URL")

        # 환경변수 오버라이드 - Redis
        if os.getenv("REDIS_HOST"):
            self.redis.host = os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            self.redis.port = int(os.getenv("REDIS_PORT"))

        # 환경변수 오버라이드 - Database
        if os.getenv("DATABASE_HOST"):
            self.database.host = os.getenv("DATABASE_HOST")
        if os.getenv("DATABASE_PORT"):
            self.database.port = int(os.getenv("DATABASE_PORT"))
        if os.getenv("DATABASE_USER"):
            self.database.user = os.getenv("DATABASE_USER")
        if os.getenv("DATABASE_PASSWORD"):
            self.database.password = os.getenv("DATABASE_PASSWORD")
        if os.getenv("DATABASE_NAME"):
            self.database.database = os.getenv("DATABASE_NAME")

        # 환경변수 오버라이드 - JWT
        if os.getenv("JWT_SECRET_KEY"):
            self.jwt.secret_key = os.getenv("JWT_SECRET_KEY")


settings = Settings()
