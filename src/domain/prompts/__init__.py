"""
Domain Prompts

도메인 지식을 담은 프롬프트 템플릿입니다.
프롬프트는 비즈니스 규칙의 일부로, Domain Layer에 속합니다.
"""
from .templates import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    GENERATOR_SYSTEM_PROMPT,
    GENERATOR_HUMAN_PROMPT,
    ROUTER_SYSTEM_PROMPT,
)

__all__ = [
    "QUERY_REWRITE_SYSTEM_PROMPT",
    "GENERATOR_SYSTEM_PROMPT",
    "GENERATOR_HUMAN_PROMPT",
    "ROUTER_SYSTEM_PROMPT",
]
