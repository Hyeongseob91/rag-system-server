"""
Configuration settings for RAG Pipeline
"""
import os
from dataclasses import dataclass, field


@dataclass
class LLMSettings:
    """LLM(API) Model Settings"""
    rewrite_model: str = "gpt-4o-mini"
    rewrite_temperature: float = 0.0
    generator_model: str = "gpt-4o"
    generator_temperature: float = 0.0


@dataclass
class VectorStoreSettings:
    """VectorDB Settings"""
    use_embedded: bool = True
    weaviate_host: str = "localhost"
    weaviate_port: int = 8080
    weaviate_grpc_port: int = 50051
    weaviate_version: str = "1.27.0"
    data_path: str = "./weaviate_data"
    collection_name: str = "RAG_Chunk"
    embedding_model: str = "text-embedding-3-small"
    bm25_b: float = 0.75
    bm25_k1: float = 1.2


@dataclass
class RerankerSettings:
    """Reranker 관련 설정"""
    model_name: str = "BAAI/bge-reranker-v2-m3"
    top_k: int = 5


@dataclass
class RetrieverSettings:
    """Retriever 관련 설정"""
    hybrid_alpha: float = 0.5
    initial_limit: int = 30


@dataclass
class PreprocessingSettings:
    """전처리 관련 설정"""
    embedding_model: str = "text-embedding-3-small"
    breakpoint_type: str = "percentile"
    breakpoint_threshold: float = 95.0
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    remove_extra_whitespace: bool = True
    remove_extra_newlines: bool = True
    remove_special_chars: bool = False
    min_line_length: int = 0


@dataclass
class Settings:
    """전체 설정 관리"""
    llm: LLMSettings = field(default_factory=LLMSettings)
    vectorstore: VectorStoreSettings = field(default_factory=VectorStoreSettings)
    reranker: RerankerSettings = field(default_factory=RerankerSettings)
    retriever: RetrieverSettings = field(default_factory=RetrieverSettings)
    preprocessing: PreprocessingSettings = field(default_factory=PreprocessingSettings)

    def __post_init__(self):
        if os.getenv("WEAVIATE_USE_EMBEDDED"):
            self.vectorstore.use_embedded = os.getenv("WEAVIATE_USE_EMBEDDED").lower() == "true"
        if os.getenv("WEAVIATE_HOST"):
            self.vectorstore.weaviate_host = os.getenv("WEAVIATE_HOST")
        if os.getenv("WEAVIATE_PORT"):
            self.vectorstore.weaviate_port = int(os.getenv("WEAVIATE_PORT"))
        if os.getenv("WEAVIATE_GRPC_PORT"):
            self.vectorstore.weaviate_grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT"))
        if os.getenv("WEAVIATE_DATA_PATH"):
            self.vectorstore.data_path = os.getenv("WEAVIATE_DATA_PATH")


settings = Settings()
