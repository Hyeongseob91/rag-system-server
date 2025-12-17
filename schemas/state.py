"""Graph State Schemas for RAG Pipeline"""
from typing import List, TypedDict


class RAGState(TypedDict):
    question: str
    optimized_queries: List[str]
    retrieved_docs: List[str]
    final_answer: str


class QueryOutput(TypedDict):
    optimized_queries: List[str]


class RetrievalOutput(TypedDict):
    retrieved_docs: List[str]


class GenerationOutput(TypedDict):
    final_answer: str
