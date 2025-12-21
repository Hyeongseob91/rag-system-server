"""
Authentication Routes

Presentation Layer: 인증 관련 API 엔드포인트
- POST /api/v1/auth/register: 회원가입
- POST /api/v1/auth/login: 로그인
- GET /api/v1/auth/me: 현재 사용자 정보
"""
from fastapi import APIRouter, Depends, HTTPException, status

from src.presentation.dto.schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    ErrorResponse
)
from src.presentation.api.dependencies import get_rag_app, get_current_user
from src.domain.entities import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "이미 존재하는 사용자"},
    }
)
async def register(request: RegisterRequest, app=Depends(get_rag_app)):
    """회원가입

    새 사용자를 등록하고 JWT 토큰을 반환합니다.
    """
    # 사용자 이름 중복 확인
    if app.user_repo.exists(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자 이름입니다."
        )

    # 비밀번호 해시 및 사용자 생성
    password_hash = app.auth_service.hash_password(request.password)
    user = app.user_repo.create(request.username, password_hash)

    # JWT 토큰 생성
    token = app.auth_service.create_access_token(user.id, user.username)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 실패"},
    }
)
async def login(request: LoginRequest, app=Depends(get_rag_app)):
    """로그인

    사용자 인증 후 JWT 토큰을 반환합니다.
    """
    # 사용자 조회
    user = app.user_repo.get_by_username(request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 이름 또는 비밀번호가 올바르지 않습니다."
        )

    # 비밀번호 검증
    if not app.auth_service.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 이름 또는 비밀번호가 올바르지 않습니다."
        )

    # 활성 사용자 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비활성화된 계정입니다."
        )

    # JWT 토큰 생성
    token = app.auth_service.create_access_token(user.id, user.username)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "인증 필요"},
    }
)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보

    JWT 토큰으로 인증된 현재 사용자 정보를 반환합니다.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )
