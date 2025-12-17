"""Reranker Service - Cross-Encoder"""
from typing import List, Tuple
from sentence_transformers import CrossEncoder
from ..config import Settings


class RerankerService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: CrossEncoder = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(self.settings.reranker.model_name)
        return self._model

    def rerank(self, query: str, documents: List[str], top_k: int = None) -> List[Tuple[str, float]]:
        if top_k is None:
            top_k = self.settings.reranker.top_k
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def get_top_documents(self, query: str, documents: List[str], top_k: int = None) -> List[Tuple[str, float]]:
        return self.rerank(query, documents, top_k)
