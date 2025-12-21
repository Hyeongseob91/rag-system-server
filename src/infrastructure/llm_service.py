"""
LLM Service - OpenAI API 연동

Infrastructure Layer: 외부 LLM 서비스와의 통신을 담당합니다.
"""
from typing import Type, TypeVar
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from src.core import Settings

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """OpenAI LLM 서비스

    OpenAI API를 통한 LLM 호출을 담당합니다.
    - Query Rewrite용 LLM (빠르고 저렴한 모델)
    - Generator용 LLM (고성능 모델)
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def get_rewrite_llm(self) -> ChatOpenAI:
        """Query Rewrite용 LLM 반환"""
        return ChatOpenAI(
            model=self.settings.llm.rewrite_model,
            temperature=self.settings.llm.rewrite_temperature,
        )

    def get_generator_llm(self) -> ChatOpenAI:
        """Generator용 LLM 반환"""
        return ChatOpenAI(
            model=self.settings.llm.generator_model,
            temperature=self.settings.llm.generator_temperature,
        )

    def invoke_with_structured_output(
        self, llm: ChatOpenAI, prompt: ChatPromptTemplate, output_schema: Type[T], input_data: dict
    ) -> T:
        """구조화된 출력으로 LLM 호출"""
        structured_llm = llm.with_structured_output(output_schema)
        chain = prompt | structured_llm
        return chain.invoke(input_data)

    def invoke_with_string_output(
        self, llm: ChatOpenAI, prompt: ChatPromptTemplate, input_data: dict
    ) -> str:
        """문자열 출력으로 LLM 호출"""
        chain = prompt | llm | StrOutputParser()
        return chain.invoke(input_data)
