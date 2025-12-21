"""Preprocessing Pipeline"""
import uuid
from pathlib import Path
from typing import List

from ...config import Settings
from ...schemas.preprocessing import Chunk, DocumentMetadata, PreprocessingResult, RawDocument
from .chunking import ChunkingService
from .normalizer import TextNormalizer
from .parsers import UnifiedFileParser


class PreprocessingPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._parser = UnifiedFileParser()
        self._normalizer = TextNormalizer(settings)
        self._chunking_service = ChunkingService(settings)

    def process_file(self, file_path: str) -> PreprocessingResult:
        try:
            # max_pages 설정 적용 (0이면 전체 페이지)
            max_pages = self.settings.preprocessing.max_pages or None
            raw_doc = self._parser.parse(file_path, max_pages=max_pages)
            normalized_doc = self._normalizer.normalize_document(raw_doc)
            chunks = self._chunking_service.chunk_document(normalized_doc)
            for chunk in chunks:
                chunk.metadata["total_chunks"] = len(chunks)

            doc_metadata = DocumentMetadata(
                doc_id=chunks[0].doc_id if chunks else str(uuid.uuid4()),
                source=normalized_doc.source,
                file_name=normalized_doc.file_name,
                file_type=normalized_doc.file_type,
                file_size=normalized_doc.metadata.get("file_size", 0),
                page_count=normalized_doc.metadata.get("page_count"),
                sheet_count=normalized_doc.metadata.get("sheet_count"),
            )
            stats = self._chunking_service.get_chunk_stats(chunks)
            stats["original_length"] = len(raw_doc.content)
            stats["normalized_length"] = len(normalized_doc.content)
            return PreprocessingResult(document=normalized_doc, chunks=chunks, metadata=doc_metadata, stats=stats, success=True)
        except Exception as e:
            return PreprocessingResult(document=None, chunks=[], metadata=None, stats={}, success=False, error=str(e))

    def process_directory(self, dir_path: str, recursive: bool = False) -> List[PreprocessingResult]:
        results = []
        pattern = "**/*" if recursive else "*"
        for file_path in Path(dir_path).glob(pattern):
            if file_path.is_file() and file_path.suffix.lower().lstrip(".") in self._parser.get_supported_extensions():
                result = self.process_file(str(file_path))
                results.append(result)
                print(f"{'✓' if result.success else '✗'} {file_path.name}: {result.stats.get('count', 0)}개 청크" if result.success else result.error)
        return results

    def get_supported_extensions(self) -> List[str]:
        return self._parser.get_supported_extensions()
