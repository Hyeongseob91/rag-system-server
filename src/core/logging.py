"""
Logging configuration for RAG Pipeline

Cross-cutting concern: 모든 레이어에서 사용하는 로깅 설정
"""
import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.DEBUG,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    애플리케이션 전역 로깅 설정

    Args:
        level: 로깅 레벨 (기본: DEBUG)
        log_format: 로그 포맷 (기본: 상세 포맷)
        log_file: 로그 파일 경로 (선택사항)
    """
    if log_format is None:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
        )

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (선택사항)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("qdrant_client").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 획득

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        Logger 인스턴스

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
        logger.debug("Details: %s", data)
    """
    return logging.getLogger(name)


# 기본 로깅 초기화 (import 시 자동 실행)
setup_logging()
