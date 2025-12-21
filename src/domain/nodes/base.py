"""
Base Node

모든 노드의 기본 인터페이스를 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

from src.application.state import RAGState


class BaseNode(ABC):
    """노드 기본 클래스

    모든 RAG 노드는 이 클래스를 상속받습니다.
    LangGraph에서 노드로 사용되기 위한 인터페이스를 정의합니다.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """노드 이름 (LangGraph에서 사용)"""
        pass

    @abstractmethod
    def __call__(self, state: RAGState) -> Dict[str, Any]:
        """노드 실행

        Args:
            state: 현재 워크플로우 상태

        Returns:
            상태 업데이트 딕셔너리
        """
        pass
