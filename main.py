"""
RAG Pipeline - Entry Point

Layered Architecture 기반 RAG 시스템

Layers:
- Presentation: HTTP API (FastAPI)
- Application: 워크플로우 (LangGraph)
- Domain: 비즈니스 로직 (Nodes, Entities)
- Infrastructure: 외부 시스템 (OpenAI, Qdrant, Infinity)
- Core: 공통 설정

Usage:
    # CLI 모드
    python main.py

    # API 서버 모드
    uvicorn src.presentation.api.main:app --reload
"""
from dotenv import load_dotenv
from src.application import RAGApplication, create_app


if __name__ == "__main__":
    load_dotenv()
    app = create_app().initialize()
    print(f"\n질문: RAG 성능 고도화의 개념은?\n")
    print(f"답변:\n{app.run('RAG 성능 고도화의 개념은?')}")
    app.close()
