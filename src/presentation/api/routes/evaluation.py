"""
Evaluation Endpoint

Presentation Layer: RAG 평가 API

엔드포인트:
- POST /api/v1/eval/single: 단일 쿼리 평가
- POST /api/v1/eval/batch: 배치 평가
- GET /api/v1/eval/profiles: 사용 가능한 프로파일 목록
- POST /api/v1/eval/export: 결과 내보내기
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.core.profiles import list_profile_summaries, get_profile, PROFILES
from src.presentation.api.dependencies import get_rag_app
from src.evaluation import (
    EvaluationRunner,
    EvaluationRequest,
    EvaluationResult,
    BatchEvaluationRequest,
    BatchEvaluationResult,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/eval", tags=["Evaluation"])


# ============ Request/Response DTOs ============

class SingleEvalRequest(BaseModel):
    """단일 평가 요청"""
    question: str = Field(..., description="평가할 질문")
    ground_truth: Optional[str] = Field(None, description="정답 (Generation 평가용)")
    relevant_doc_ids: Optional[List[str]] = Field(None, description="관련 문서 ID 목록")
    profile_id: str = Field("hybrid_rerank", description="프로파일 ID")
    include_generation_metrics: bool = Field(True, description="RAGAS 메트릭 포함 (시간 소요)")


class BatchEvalRequest(BaseModel):
    """배치 평가 요청"""
    items: List[SingleEvalRequest] = Field(..., description="평가할 항목들")
    profile_id: str = Field("hybrid_rerank", description="공통 프로파일 ID")
    include_generation_metrics: bool = Field(True, description="RAGAS 메트릭 포함")


class ProfileInfo(BaseModel):
    """프로파일 정보"""
    id: str
    name: str
    description: str
    retriever_type: str
    use_reranker: bool
    use_query_rewrite: bool


class ExportRequest(BaseModel):
    """내보내기 요청"""
    results: List[EvaluationResult]
    format: str = Field("json", description="json 또는 csv")


# ============ Endpoints ============

@router.post("/single", response_model=EvaluationResult)
async def evaluate_single(
    request: SingleEvalRequest,
    rag_app=Depends(get_rag_app),
):
    """
    단일 쿼리 평가

    RAG 파이프라인을 실행하고 다양한 메트릭을 계산합니다.

    - **question**: 평가할 질문
    - **ground_truth**: 정답 (선택사항, RAGAS context_recall 계산에 필요)
    - **relevant_doc_ids**: 관련 문서 ID 목록 (선택사항, Retrieval 메트릭 계산에 필요)
    - **profile_id**: 사용할 실험 프로파일
    - **include_generation_metrics**: RAGAS 메트릭 포함 여부 (추가 LLM 호출 발생)
    """
    logger.info("[Eval] 단일 평가 요청: profile=%s, question=%s",
               request.profile_id, request.question[:50])

    try:
        # 프로파일 유효성 검사
        if request.profile_id not in PROFILES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown profile: {request.profile_id}. Available: {list(PROFILES.keys())}"
            )

        runner = EvaluationRunner(app=rag_app)

        eval_request = EvaluationRequest(
            question=request.question,
            ground_truth=request.ground_truth,
            relevant_doc_ids=request.relevant_doc_ids,
            profile_id=request.profile_id,
        )

        result = runner.evaluate_single(
            request=eval_request,
            include_generation_metrics=request.include_generation_metrics,
        )

        logger.info("[Eval] 평가 완료: latency=%.1fms", result.latency.total_ms)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[Eval] 평가 실패: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchEvaluationResult)
async def evaluate_batch(
    request: BatchEvalRequest,
    rag_app=Depends(get_rag_app),
):
    """
    배치 평가

    여러 질문을 한 번에 평가하고 집계된 메트릭을 반환합니다.

    - **items**: 평가할 항목 리스트
    - **profile_id**: 공통 프로파일 (개별 항목 설정 우선)
    - **include_generation_metrics**: RAGAS 메트릭 포함 여부
    """
    logger.info("[Eval] 배치 평가 요청: %d개 항목, profile=%s",
               len(request.items), request.profile_id)

    try:
        runner = EvaluationRunner(app=rag_app)

        batch_request = BatchEvaluationRequest(
            items=[
                EvaluationRequest(
                    question=item.question,
                    ground_truth=item.ground_truth,
                    relevant_doc_ids=item.relevant_doc_ids,
                    profile_id=item.profile_id or request.profile_id,
                )
                for item in request.items
            ],
            profile_id=request.profile_id,
            include_generation_metrics=request.include_generation_metrics,
        )

        result = runner.evaluate_batch(batch_request)

        logger.info("[Eval] 배치 평가 완료: %d개 완료, avg_latency=%.1fms",
                   result.aggregated.total_samples,
                   result.aggregated.avg_total_latency_ms)
        return result

    except Exception as e:
        logger.error("[Eval] 배치 평가 실패: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", response_model=List[ProfileInfo])
async def get_profiles():
    """
    사용 가능한 실험 프로파일 목록

    각 프로파일은 서로 다른 RAG 설정 조합을 정의합니다:
    - baseline: Dense 검색만 사용
    - hybrid_v1: Dense + BM25 Hybrid
    - hybrid_rerank: Full Pipeline (Hybrid + Reranker)
    - fast: 빠른 응답 우선
    """
    summaries = list_profile_summaries()
    return [ProfileInfo(**s) for s in summaries]


@router.get("/profiles/{profile_id}", response_model=ProfileInfo)
async def get_profile_detail(profile_id: str):
    """
    특정 프로파일 상세 정보
    """
    if profile_id not in PROFILES:
        raise HTTPException(
            status_code=404,
            detail=f"Profile not found: {profile_id}"
        )

    profile = get_profile(profile_id)
    return ProfileInfo(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        retriever_type=profile.retriever_type,
        use_reranker=profile.use_reranker,
        use_query_rewrite=profile.use_query_rewrite,
    )


@router.post("/export/json")
async def export_json(results: List[EvaluationResult]):
    """
    평가 결과를 JSON 파일로 내보내기
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eval_results_{timestamp}.json"

    data = [r.model_dump() for r in results]
    content = json.dumps(data, ensure_ascii=False, indent=2)

    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/csv")
async def export_csv(results: List[EvaluationResult]):
    """
    평가 결과를 CSV 파일로 내보내기
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"eval_results_{timestamp}.csv"

    # CSV 생성
    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더
    writer.writerow([
        "question",
        "answer",
        "ground_truth",
        "profile_id",
        "routing_decision",
        "recall_at_5",
        "recall_at_10",
        "ndcg_at_10",
        "mrr",
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "total_latency_ms",
        "retrieval_ms",
        "rerank_ms",
        "generation_ms",
    ])

    # 데이터
    for r in results:
        rm = r.retrieval_metrics
        gm = r.generation_metrics
        writer.writerow([
            r.question[:100],
            r.answer[:100] if r.answer else "",
            r.ground_truth[:100] if r.ground_truth else "",
            r.profile_id,
            r.routing_decision,
            rm.recall_at_5 if rm else "",
            rm.recall_at_10 if rm else "",
            rm.ndcg_at_10 if rm else "",
            rm.mrr if rm else "",
            gm.faithfulness if gm else "",
            gm.answer_relevancy if gm else "",
            gm.context_precision if gm else "",
            r.latency.total_ms,
            r.latency.retrieval_ms,
            r.latency.rerank_ms,
            r.latency.generation_ms,
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/health")
async def eval_health():
    """평가 모듈 상태 확인"""
    from src.evaluation.metrics.generation import RAGAS_AVAILABLE

    return {
        "status": "ok",
        "ragas_available": RAGAS_AVAILABLE,
        "profiles_count": len(PROFILES),
    }
