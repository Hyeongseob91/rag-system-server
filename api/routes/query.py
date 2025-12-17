"""Query Endpoint"""
import time
from fastapi import APIRouter, Depends, HTTPException
from ..schemas import QueryRequest, QueryResponse, SourceDocument, ErrorResponse
from ..dependencies import get_rag_app
from ...main import RAGApplication

router = APIRouter(prefix="/api/v1", tags=["Query"])


@router.post("/query", response_model=QueryResponse, responses={500: {"model": ErrorResponse}})
async def query(request: QueryRequest, rag_app: RAGApplication = Depends(get_rag_app)):
    start = time.time()
    try:
        result = rag_app._workflow.invoke(request.question)
        sources = [
            SourceDocument(content=doc[:500] + "..." if len(doc) > 500 else doc)
            for doc in result.get("retrieved_docs", [])[:5]
        ]
        return QueryResponse(
            answer=result["final_answer"],
            sources=sources,
            processing_time_ms=round((time.time() - start) * 1000, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "QueryProcessingError", "message": str(e)})
