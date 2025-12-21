"""
RAG Pipeline - Layered Architecture

Layers:
- presentation: HTTP API (FastAPI)
- application: 유스케이스, 워크플로우, DI Container
- domain: 비즈니스 로직, 엔티티
- infrastructure: 외부 시스템 연동
- core: 공통 설정
"""
from src.application import RAGApplication, create_app

__all__ = ["RAGApplication", "create_app"]
