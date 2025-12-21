"""
Upload Endpoint

Presentation Layer: 파일 업로드 API
- 파일 업로드 및 처리
- 캐시 무효화 (Redis)
- 문서 메타데이터 DB 저장
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks

from src.presentation.dto import UploadResponse, UploadStatusResponse, UploadStatus, ErrorResponse
from src.presentation.api.dependencies import get_rag_app, get_current_user_optional, TaskStore
from src.domain.entities import User

router = APIRouter(prefix="/api/v1", tags=["Upload"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "txt", "json"}


def validate_file_extension(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def process_file_task(
    task_id: str,
    file_path: str,
    rag_app,
    user_id: Optional[int] = None
):
    """백그라운드 파일 처리

    1. 파일 처리 (청크 생성 및 벡터 저장)
    2. Redis 캐시 전체 무효화
    3. DB에 문서 메타데이터 저장 (인증된 사용자만)
    """
    file_name = os.path.basename(file_path)

    try:
        TaskStore.update_task(task_id, status="processing")

        # 1. 파일 처리
        result = rag_app.ingest_file(file_path)

        if result.success:
            chunk_count = len(result.chunks)

            # 2. 캐시 무효화 (새 문서 추가 시 기존 캐시 무효화)
            try:
                invalidated = rag_app.cache_service.invalidate_all()
                print(f"캐시 무효화: {invalidated}개 키 삭제")
            except Exception:
                pass  # 캐시 무효화 실패해도 계속 진행

            # 3. DB에 문서 메타데이터 저장 (인증된 사용자만)
            if user_id:
                try:
                    rag_app.document_repo.create(
                        user_id=user_id,
                        file_name=file_name,
                        chunk_count=chunk_count,
                        status="completed"
                    )
                except Exception:
                    pass  # DB 저장 실패해도 계속 진행

            TaskStore.update_task(
                task_id,
                status="completed",
                chunks_created=chunk_count,
                completed_at=datetime.now()
            )
        else:
            # 처리 실패
            if user_id:
                try:
                    rag_app.document_repo.create(
                        user_id=user_id,
                        file_name=file_name,
                        chunk_count=0,
                        status="failed"
                    )
                except Exception:
                    pass

            TaskStore.update_task(
                task_id,
                status="failed",
                error=result.error,
                completed_at=datetime.now()
            )

    except Exception as e:
        TaskStore.update_task(
            task_id,
            status="failed",
            error=str(e),
            completed_at=datetime.now()
        )
    finally:
        # 임시 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload", response_model=UploadResponse, responses={400: {"model": ErrorResponse}})
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rag_app=Depends(get_rag_app),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """파일 업로드 및 처리

    인증된 사용자의 경우 문서 메타데이터가 DB에 저장됩니다.
    """
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail={"error": "InvalidFileType", "message": f"허용: {ALLOWED_EXTENSIONS}"}
        )

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task_id = TaskStore.create_task(file.filename)

    # user_id 전달 (인증된 사용자만)
    user_id = current_user.id if current_user else None
    background_tasks.add_task(process_file_task, task_id, str(file_path), rag_app, user_id)

    return UploadResponse(
        task_id=task_id,
        file_name=file.filename,
        status=UploadStatus.PENDING,
        message="파일 업로드 완료. 백그라운드 처리 중."
    )


@router.get("/upload/{task_id}", response_model=UploadStatusResponse, responses={404: {"model": ErrorResponse}})
async def get_upload_status(task_id: str):
    """업로드 상태 조회"""
    task = TaskStore.get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "TaskNotFound", "message": f"작업 ID를 찾을 수 없습니다: {task_id}"}
        )
    return UploadStatusResponse(
        task_id=task.task_id,
        status=UploadStatus(task.status),
        file_name=task.file_name,
        chunks_created=task.chunks_created,
        error=task.error,
        completed_at=task.completed_at
    )
