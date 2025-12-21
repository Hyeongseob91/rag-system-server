"""
Query Rewrite Node

Domain Layer: 사용자 질문을 검색에 최적화된 쿼리로 변환합니다.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base import BaseNode
from src.application.state import RAGState
from src.domain.entities import RewriteResult
from src.domain.prompts import QUERY_REWRITE_SYSTEM_PROMPT
from src.infrastructure import LLMService


class QueryRewriteNode(BaseNode):
    """쿼리 리라이트 노드

    왜 필요한가?
    - 사용자 질문은 종종 모호하거나 검색에 최적화되지 않음
    - "이거 뭐야?" → 무엇이 "이것"인지 불명확
    - 다각도 쿼리 생성으로 검색 재현율 향상
    """

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", QUERY_REWRITE_SYSTEM_PROMPT),
            ("human", "질문: {question}"),
        ])

    @property
    def name(self) -> str:
        return "query_rewrite"

    def __call__(self, state: RAGState) -> Dict[str, Any]:
        print(f"--- [Step 1] Query Rewrite 시작: {state['question']} ---")
        llm = self._llm_service.get_rewrite_llm()
        try:
            result: RewriteResult = self._llm_service.invoke_with_structured_output(
                llm=llm, prompt=self._prompt, output_schema=RewriteResult, input_data={"question": state["question"]}
            )
            print(f"--- 생성된 쿼리: {result.queries} ---")
            return {"optimized_queries": result.queries}
        except Exception as e:
            print(f"Error in Query Rewrite: {e}")
            return {"optimized_queries": [state["question"]]}
