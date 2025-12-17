"""Upload Endpoint"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from ..schemas import UploadResponse, UploadStatusResponse, UploadStatus, ErrorResponse
from ..dependencies import get_rag_app, TaskStore
from ...main import RAGApplication

router = APIRouter(prefix="/api/v1", tags=["Upload"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "txt", "json"}


def validate_file_extension(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def process_file_task(task_id: str, file_path: str, rag_app: RAGApplication):
    try:
        TaskStore.update_task(task_id, status="processing")
        result = rag_app.ingest_file(file_path)
        if result.success:
            TaskStore.update_task(task_id, status="completed", chunks_created=len(result.chunks), completed_at=datetime.now())
        else:
            TaskStore.update_task(task_id, status="failed", error=result.error, completed_at=datetime.now())
    except Exception as e:
        TaskStore.update_task(task_id, status="failed", error=str(e), completed_at=datetime.now())
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/upload", response_model=UploadResponse, responses={400: {"model": ErrorResponse}})
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), rag_app: RAGApplication = Depends(get_rag_app)):
    if not validate_file_extension(file.filename):
        raise HTTPException(status_code=400, detail={"error": "InvalidFileType", "message": f"허용: {ALLOWED_EXTENSIONS}"})
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    task_id = TaskStore.create_task(file.filename)
    background_tasks.add_task(process_file_task, task_id, str(file_path), rag_app)
    return UploadResponse(task_id=task_id, file_name=file.filename, status=UploadStatus.PENDING, message="파일 업로드 완료. 백그라운드 처리 중.")


@router.get("/upload/{task_id}", response_model=UploadStatusResponse, responses={404: {"model": ErrorResponse}})
async def get_upload_status(task_id: str):
    task = TaskStore.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail={"error": "TaskNotFound", "message": f"작업 ID를 찾을 수 없습니다: {task_id}"})
    return UploadStatusResponse(
        task_id=task.task_id, status=UploadStatus(task.status), file_name=task.file_name,
        chunks_created=task.chunks_created, error=task.error, completed_at=task.completed_at
    )
