"""
Simple Generator Node

Domain Layer: RAG 검색 없이 직접 답변을 생성합니다.
"""
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from .base import BaseNode
from src.application.state import RAGState
from src.infrastructure import LLMService


class SimpleGeneratorNode(BaseNode):
    """간단한 답변 생성 노드

    라우터가 "llm" 경로를 선택했을 때 사용됩니다.
    검색 없이 LLM이 직접 답변합니다.

    사용 케이스:
    - 인사: "안녕하세요"
    - 일반 지식: "파이썬 리스트 정렬법"
    - 요약 요청: "위 내용 정리해줘"
    """

    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 유능한 AI 어시스턴트입니다. 사용자의 질문에 친절하고 정확하게 답변하세요."),
            ("human", "{question}"),
        ])

    @property
    def name(self) -> str:
        return "simple_generator"

    def __call__(self, state: RAGState) -> Dict[str, Any]:
        print("--- [Route: LLM] 검색 없이 즉시 답변 생성 ---")
        llm = self._llm_service.get_generator_llm()
        answer = self._llm_service.invoke_with_string_output(
            llm=llm, prompt=self._prompt, input_data={"question": state["question"]}
        )
        return {"final_answer": answer}
