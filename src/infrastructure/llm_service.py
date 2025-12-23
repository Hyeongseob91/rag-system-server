"""
LLM Service - OpenAI API 연동

Infrastructure Layer: 외부 LLM 서비스와의 통신을 담당합니다.
"""
import time
from typing import Type, TypeVar
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from src.core import Settings
from src.core.logging import get_logger

T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)


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
        logger.debug("[LLM] 구조화 출력 호출: model=%s, schema=%s",
                    llm.model_name, output_schema.__name__)
        start_time = time.time()

        structured_llm = llm.with_structured_output(output_schema)
        chain = prompt | structured_llm
        result = chain.invoke(input_data)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info("[LLM] 구조화 출력 완료: model=%s (%.1fms)",
                   llm.model_name, elapsed_ms)
        return result

    def invoke_with_string_output(
        self, llm: ChatOpenAI, prompt: ChatPromptTemplate, input_data: dict
    ) -> str:
        """문자열 출력으로 LLM 호출"""
        logger.debug("[LLM] 문자열 출력 호출: model=%s", llm.model_name)
        start_time = time.time()

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke(input_data)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info("[LLM] 문자열 출력 완료: model=%s, 길이=%d (%.1fms)",
                   llm.model_name, len(result), elapsed_ms)
        return result
