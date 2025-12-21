"""
Query Endpoint

Presentation Layer: 질문 처리 API
- 캐시 확인 (Redis)
- RAG 파이프라인 실행
- 결과 캐싱 및 DB 저장
"""
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.presentation.dto import QueryRequest, QueryResponse, SourceDocument, ErrorResponse
from src.presentation.api.dependencies import get_rag_app, get_current_user_optional
from src.domain.entities import User

router = APIRouter(prefix="/api/v1", tags=["Query"])


@router.post("/query", response_model=QueryResponse, responses={500: {"model": ErrorResponse}})
async def query(
    request: QueryRequest,
    rag_app=Depends(get_rag_app),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """질문에 대한 답변 생성

    1. Redis 캐시 확인 → 히트 시 즉시 반환
    2. RAG 파이프라인 실행
    3. 결과 캐싱 (Redis) + DB 저장 (인증된 사용자만)
    """
    start = time.time()

    try:
        # 1. 캐시 확인
        cached = rag_app.cache_service.get_cached_response(request.question)
        if cached:
            # 캐시 히트 - DB에는 저장하지 않음 (이미 저장됨)
            return QueryResponse(
                answer=cached["answer"],
                sources=[SourceDocument(**s) for s in cached.get("sources", [])],
                processing_time_ms=cached.get("processing_time_ms", 0),
                cached=True
            )

        # 2. RAG 파이프라인 실행
        result = rag_app._workflow.invoke(request.question)

        # 출처 문서 정리
        sources = [
            SourceDocument(content=doc[:500] + "..." if len(doc) > 500 else doc)
            for doc in result.get("retrieved_docs", [])[:5]
        ]

        processing_time_ms = round((time.time() - start) * 1000, 2)
        answer = result["final_answer"]

        # 3. 캐시 저장
        rag_app.cache_service.cache_response(
            question=request.question,
            answer=answer,
            sources=[s.model_dump() for s in sources],
            processing_time_ms=processing_time_ms
        )

        # 4. DB 저장 (인증된 사용자만)
        if current_user:
            try:
                rag_app.conversation_repo.create(
                    user_id=current_user.id,
                    question=request.question,
                    answer=answer,
                    sources=[s.model_dump() for s in sources],
                    routing_decision=result.get("routing_decision"),
                    processing_time_ms=processing_time_ms
                )
            except Exception:
                # DB 저장 실패해도 응답은 반환
                pass

        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time_ms=processing_time_ms,
            cached=False
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "QueryProcessingError", "message": str(e)})
