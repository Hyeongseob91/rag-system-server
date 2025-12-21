"""
FastAPI Dependencies

Presentation Layer: 의존성 주입 및 생명주기 관리
"""
import uuid
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core import Settings
from src.domain.entities import User


# OAuth2 스키마 (토큰 URL 지정)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class RAGAppManager:
    """RAGApplication 싱글톤 관리자"""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise RuntimeError("RAGApplication이 초기화되지 않았습니다.")
        return cls._instance

    @classmethod
    def initialize(cls, settings: Settings = None):
        # 순환 import 방지를 위해 여기서 import
        from src.application.container import RAGApplication
        load_dotenv()
        cls._instance = RAGApplication(settings)
        cls._instance.initialize(create_collection=False)
        return cls._instance

    @classmethod
    def shutdown(cls) -> None:
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None


def get_rag_app():
    """RAGApplication 의존성"""
    return RAGAppManager.get_instance()


class TaskStatus:
    """업로드 작업 상태"""
    def __init__(self, task_id: str, file_name: str):
        self.task_id = task_id
        self.file_name = file_name
        self.status = "pending"
        self.chunks_created: Optional[int] = None
        self.error: Optional[str] = None
        self.completed_at: Optional[datetime] = None


class TaskStore:
    """업로드 작업 저장소 (메모리 기반)"""
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
    """FastAPI 생명주기 관리"""
    print("=== RAG API Server Starting ===")
    RAGAppManager.initialize()
    print("=== RAGApplication Initialized ===")
    yield
    print("=== RAG API Server Shutting Down ===")
    RAGAppManager.shutdown()


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    app=Depends(get_rag_app)
) -> User:
    """현재 인증된 사용자 조회

    JWT 토큰을 검증하고 사용자 정보를 반환합니다.

    Raises:
        HTTPException: 인증 실패 시 401 에러
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 토큰에서 user_id 추출
    user_id = app.auth_service.get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 조회
    user = app.user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    app=Depends(get_rag_app)
) -> Optional[User]:
    """현재 인증된 사용자 조회 (선택적)

    인증되지 않은 경우 None을 반환합니다.
    """
    if not token:
        return None

    user_id = app.auth_service.get_user_id_from_token(token)
    if not user_id:
        return None

    user = app.user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user
