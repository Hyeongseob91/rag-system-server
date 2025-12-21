"""
Text Normalizer

Infrastructure Layer: 텍스트 정규화
"""
import re
from src.core import Settings
from src.domain.entities import RawDocument


class TextNormalizer:
    """텍스트 정규화 서비스

    파싱된 텍스트를 정규화합니다.
    - 불필요한 공백/줄바꿈 제거
    - 특수문자 처리
    - 최소 라인 길이 필터링
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._config = settings.preprocessing

    def normalize(self, text: str) -> str:
        """텍스트 정규화"""
        result = text
        if self._config.remove_extra_newlines:
            result = re.sub(r"\n{3,}", "\n\n", result)
        if self._config.remove_extra_whitespace:
            result = re.sub(r"[ \t]+", " ", result)
            result = re.sub(r" +\n", "\n", result)
        if self._config.remove_special_chars:
            result = re.sub(r"[^가-힣a-zA-Z0-9\s.,!?\-:;()\[\]\"']", "", result)
        if self._config.min_line_length > 0:
            lines = [l for l in result.split("\n") if len(l.strip()) >= self._config.min_line_length or l.strip() == ""]
            result = "\n".join(lines)
        return result.strip()

    def normalize_document(self, doc: RawDocument) -> RawDocument:
        """문서 전체 정규화"""
        return RawDocument(
            content=self.normalize(doc.content),
            source=doc.source,
            file_type=doc.file_type,
            file_name=doc.file_name,
            metadata={**doc.metadata, "normalized": True},
            pages=[self.normalize(p) for p in doc.pages] if doc.pages else None,
            sheets={k: self.normalize(v) for k, v in doc.sheets.items()} if doc.sheets else None,
        )
