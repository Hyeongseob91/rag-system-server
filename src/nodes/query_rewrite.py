"""Query Rewrite Node"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseNode
from ..schemas import RAGState, RewriteResult
from ..services import LLMService
from ..prompts import QUERY_REWRITE_SYSTEM_PROMPT


class QueryRewriteNode(BaseNode):
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
