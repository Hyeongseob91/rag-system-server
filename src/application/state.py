"""
Workflow State

Application Layer: 워크플로우 상태를 정의합니다.
LangGraph의 StateGraph에서 사용됩니다.
"""
from typing import List, TypedDict


class RAGState(TypedDict):
    """RAG 워크플로우 상태

    LangGraph StateGraph를 통해 각 노드 간에 전달되는 상태입니다.

    Attributes:
        question: 사용자 질문
        optimized_queries: Query Rewrite 노드 출력
        retrieved_docs: Retriever 노드 출력
        final_answer: Generator 노드 출력
    """
    question: str
    optimized_queries: List[str]
    retrieved_docs: List[str]
    final_answer: str


class QueryOutput(TypedDict):
    """Query Rewrite 노드 출력"""
    optimized_queries: List[str]


class RetrievalOutput(TypedDict):
    """Retriever 노드 출력"""
    retrieved_docs: List[str]


class GenerationOutput(TypedDict):
    """Generator 노드 출력"""
    final_answer: str
