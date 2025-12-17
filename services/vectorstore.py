"""VectorStore Service - Weaviate"""
import os
from typing import TYPE_CHECKING, List, Optional

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import MetadataQuery

from ..config import Settings

if TYPE_CHECKING:
    from ..schemas.preprocessing import Chunk


class VectorStoreService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Optional[weaviate.WeaviateClient] = None
        self._collection = None

    @property
    def client(self) -> weaviate.WeaviateClient:
        if self._client is None:
            self._connect()
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.collections.get(self.settings.vectorstore.collection_name)
        return self._collection

    def _connect(self) -> None:
        vs = self.settings.vectorstore
        if vs.use_embedded:
            if not os.path.exists(vs.data_path):
                os.makedirs(vs.data_path)
            self._client = weaviate.connect_to_embedded(
                version=vs.weaviate_version,
                persistence_data_path=vs.data_path,
                headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")},
                environment_variables={
                    "ENABLE_MODULES": "text2vec-openai",
                    "DEFAULT_VECTORIZER_MODULE": "text2vec-openai",
                },
            )
        else:
            self._client = weaviate.connect_to_local(
                host=vs.weaviate_host,
                port=vs.weaviate_port,
                grpc_port=vs.weaviate_grpc_port,
                headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")},
            )

    def is_ready(self) -> bool:
        return self.client.is_ready()

    def close(self) -> None:
        if self._client is not None and self._client.is_connected():
            self._client.close()
            self._client = None
            self._collection = None

    def create_collection(self, extended_schema: bool = True) -> None:
        name = self.settings.vectorstore.collection_name
        if self.client.collections.exists(name):
            self.client.collections.delete(name)

        properties = [Property(name="content", data_type=DataType.TEXT)]
        if extended_schema:
            properties.extend([
                Property(name="chunk_id", data_type=DataType.TEXT),
                Property(name="doc_id", data_type=DataType.TEXT),
                Property(name="chunk_index", data_type=DataType.INT),
                Property(name="total_chunks", data_type=DataType.INT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="file_name", data_type=DataType.TEXT),
                Property(name="file_type", data_type=DataType.TEXT),
                Property(name="char_count", data_type=DataType.INT),
                Property(name="page_number", data_type=DataType.INT),
                Property(name="sheet_name", data_type=DataType.TEXT),
                Property(name="created_at", data_type=DataType.DATE),
            ])

        self._collection = self.client.collections.create(
            name=name,
            vectorizer_config=Configure.Vectorizer.text2vec_openai(
                model=self.settings.vectorstore.embedding_model
            ),
            inverted_index_config=Configure.inverted_index(
                bm25_b=self.settings.vectorstore.bm25_b,
                bm25_k1=self.settings.vectorstore.bm25_k1,
            ),
            properties=properties,
        )

    def add_chunks(self, chunks: List["Chunk"]) -> int:
        added = 0
        with self.collection.batch.dynamic() as batch:
            for chunk in chunks:
                batch.add_object(properties=chunk.to_weaviate_object())
                added += 1
        return added

    def get_document_count(self) -> int:
        result = self.collection.aggregate.over_all(total_count=True)
        return result.total_count or 0

    def hybrid_search(self, query: str, alpha: Optional[float] = None, limit: Optional[int] = None) -> List[str]:
        if alpha is None:
            alpha = self.settings.retriever.hybrid_alpha
        if limit is None:
            limit = self.settings.retriever.initial_limit

        response = self.collection.query.hybrid(
            query=query, alpha=alpha, limit=limit, return_metadata=MetadataQuery(score=True)
        )
        return [obj.properties["content"] for obj in response.objects]
