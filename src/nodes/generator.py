"""Generator Node"""
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from .base import BaseNode
from ..schemas import RAGState
from ..services import LLMService
from ..prompts import GENERATOR_SYSTEM_PROMPT, GENERATOR_HUMAN_PROMPT


class GeneratorNode(BaseNode):
    def __init__(self, llm_service: LLMService):
        self._llm_service = llm_service
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", GENERATOR_SYSTEM_PROMPT),
            ("human", GENERATOR_HUMAN_PROMPT)
        ])

    @property
    def name(self) -> str:
        return "generator"

    def _format_docs(self, docs: List[str]) -> str:
        return "\n\n".join(f"[{i+1}] {doc}" for i, doc in enumerate(docs))

    def __call__(self, state: RAGState) -> Dict[str, Any]:
        print("--- [Step 3] Generator 시작 ---")
        docs = state.get("retrieved_docs", [])
        if not docs:
            return {"final_answer": "검색된 문서가 없어 답변을 생성할 수 없습니다."}

        llm = self._llm_service.get_generator_llm()
        response = self._llm_service.invoke_with_string_output(
            llm=llm, prompt=self._prompt,
            input_data={"question": state["question"], "context": self._format_docs(docs)}
        )
        print(f"--- 생성 완료: {response[:50]}... ---")
        return {"final_answer": response}
