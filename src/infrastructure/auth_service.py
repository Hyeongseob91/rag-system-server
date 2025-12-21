"""
Authentication Service

Infrastructure Layer: JWT 토큰 기반 인증
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from src.core import Settings


class AuthService:
    """JWT 인증 서비스"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """비밀번호 해시 생성

        Args:
            password: 평문 비밀번호

        Returns:
            bcrypt 해시된 비밀번호
        """
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증

        Args:
            plain_password: 평문 비밀번호
            hashed_password: 해시된 비밀번호

        Returns:
            일치 여부
        """
        return self._pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user_id: int, username: str) -> str:
        """JWT 액세스 토큰 생성

        Args:
            user_id: 사용자 ID
            username: 사용자 이름

        Returns:
            JWT 토큰 문자열
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.settings.jwt.expire_minutes
        )
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(
            payload,
            self.settings.jwt.secret_key,
            algorithm=self.settings.jwt.algorithm
        )

    def decode_token(self, token: str) -> Optional[dict]:
        """JWT 토큰 디코딩

        Args:
            token: JWT 토큰 문자열

        Returns:
            디코딩된 페이로드 또는 None (유효하지 않은 경우)
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt.secret_key,
                algorithms=[self.settings.jwt.algorithm]
            )
            return payload
        except JWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[int]:
        """토큰에서 user_id 추출

        Args:
            token: JWT 토큰 문자열

        Returns:
            user_id 또는 None
        """
        payload = self.decode_token(token)
        if payload and "sub" in payload:
            try:
                return int(payload["sub"])
            except (ValueError, TypeError):
                return None
        return None
