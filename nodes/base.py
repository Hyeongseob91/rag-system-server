"""Base Node"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from ..schemas import RAGState


class BaseNode(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def __call__(self, state: RAGState) -> Dict[str, Any]:
        pass
