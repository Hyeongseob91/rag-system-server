"""
Admin Endpoints

Presentation Layer: 관리 API (헬스체크, 컬렉션 관리)
"""
from fastapi import APIRouter, Depends, HTTPException

from src.presentation.dto import HealthResponse, CollectionsResponse, CollectionInfo, CollectionDeleteResponse, ErrorResponse
from src.presentation.api.dependencies import get_rag_app

router = APIRouter(prefix="/api/v1", tags=["Admin"])


@router.get("/health", response_model=HealthResponse)
async def health_check(rag_app=Depends(get_rag_app)):
    """상세 헬스 체크"""
    try:
        connected = rag_app.vectorstore.is_ready()
        doc_count = rag_app.vectorstore.get_document_count() if connected else 0
    except Exception:
        connected, doc_count = False, 0
    return HealthResponse(
        status="healthy" if connected else "degraded",
        qdrant_connected=connected,
        document_count=doc_count,
        version="2.0.0",
    )


@router.get("/collections", response_model=CollectionsResponse)
async def list_collections(rag_app=Depends(get_rag_app)):
    """컬렉션 목록 조회"""
    try:
        name = rag_app.settings.vectorstore.collection_name
        is_ready = rag_app.vectorstore.is_ready()
        doc_count = rag_app.vectorstore.get_document_count() if is_ready else 0
        return CollectionsResponse(collections=[CollectionInfo(name=name, document_count=doc_count, is_ready=is_ready)])
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "CollectionError", "message": str(e)})


@router.delete("/collection/{name}", response_model=CollectionDeleteResponse, responses={404: {"model": ErrorResponse}})
async def delete_collection(name: str, rag_app=Depends(get_rag_app)):
    """컬렉션 삭제 (재생성)"""
    current = rag_app.settings.vectorstore.collection_name
    if name != current:
        raise HTTPException(status_code=404, detail={"error": "CollectionNotFound", "message": f"컬렉션 없음: {name}"})
    rag_app.vectorstore.create_collection()
    return CollectionDeleteResponse(success=True, message="컬렉션이 재생성되었습니다.", deleted_collection=name)
