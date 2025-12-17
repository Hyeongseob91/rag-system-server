"""FastAPI Dependencies"""
import uuid
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv

from ..main import RAGApplication
from ..config import Settings


class RAGAppManager:
    _instance: Optional[RAGApplication] = None

    @classmethod
    def get_instance(cls) -> RAGApplication:
        if cls._instance is None:
            raise RuntimeError("RAGApplication이 초기화되지 않았습니다.")
        return cls._instance

    @classmethod
    def initialize(cls, settings: Settings = None) -> RAGApplication:
        load_dotenv()
        cls._instance = RAGApplication(settings)
        cls._instance.initialize(create_collection=False)
        return cls._instance

    @classmethod
    def shutdown(cls) -> None:
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None


def get_rag_app() -> RAGApplication:
    return RAGAppManager.get_instance()


class TaskStatus:
    def __init__(self, task_id: str, file_name: str):
        self.task_id = task_id
        self.file_name = file_name
        self.status = "pending"
        self.chunks_created: Optional[int] = None
        self.error: Optional[str] = None
        self.completed_at: Optional[datetime] = None


class TaskStore:
    _tasks: Dict[str, TaskStatus] = {}

    @classmethod
    def create_task(cls, file_name: str) -> str:
        task_id = str(uuid.uuid4())
        cls._tasks[task_id] = TaskStatus(task_id, file_name)
        return task_id

    @classmethod
    def get_task(cls, task_id: str) -> Optional[TaskStatus]:
        return cls._tasks.get(task_id)

    @classmethod
    def update_task(cls, task_id: str, **kwargs) -> None:
        if task_id in cls._tasks:
            for k, v in kwargs.items():
                setattr(cls._tasks[task_id], k, v)


@asynccontextmanager
async def lifespan(app):
    print("=== RAG API Server Starting ===")
    RAGAppManager.initialize()
    print("=== RAGApplication Initialized ===")
    yield
    print("=== RAG API Server Shutting Down ===")
    RAGAppManager.shutdown()
