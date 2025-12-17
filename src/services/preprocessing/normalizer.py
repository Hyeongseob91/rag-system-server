"""Text Normalizer"""
import re
from ...config import Settings
from ...schemas.preprocessing import RawDocument


class TextNormalizer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._config = settings.preprocessing

    def normalize(self, text: str) -> str:
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
        return RawDocument(
            content=self.normalize(doc.content),
            source=doc.source,
            file_type=doc.file_type,
            file_name=doc.file_name,
            metadata={**doc.metadata, "normalized": True},
            pages=[self.normalize(p) for p in doc.pages] if doc.pages else None,
            sheets={k: self.normalize(v) for k, v in doc.sheets.items()} if doc.sheets else None,
        )
