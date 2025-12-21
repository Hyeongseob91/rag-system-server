"""
Chunking Service - Semantic Chunking

Infrastructure Layer: 의미 기반 청크 분할
"""
import uuid
from typing import Any, Dict, List

from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from src.core import Settings
from src.domain.entities import Chunk, RawDocument


class ChunkingService:
    """Semantic Chunking 서비스

    왜 Semantic Chunking인가?
    - 고정 크기 분할: 문장 중간에서 끊김, 문맥 손실
    - Semantic Chunking: 의미 경계에서 분할, 문맥 보존

    임베딩 기반으로 의미적 유사도를 계산하여
    적절한 분할 지점을 찾습니다.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._config = settings.preprocessing
        self._embeddings = None
        self._chunker = None

    def _initialize(self):
        """Lazy initialization"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model=self._config.embedding_model)
            self._chunker = SemanticChunker(
                embeddings=self._embeddings,
                breakpoint_threshold_type=self._config.breakpoint_type,
                breakpoint_threshold_amount=self._config.breakpoint_threshold,
            )

    def chunk_text(self, text: str, doc_id: str, source: str, file_name: str, file_type: str) -> List[Chunk]:
        """텍스트를 청크로 분할"""
        self._initialize()
        docs = self._chunker.create_documents([text])
        chunks = []
        for i, doc in enumerate(docs):
            chunks.append(Chunk(
                content=doc.page_content,
                chunk_id=str(uuid.uuid4()),
                chunk_index=i,
                doc_id=doc_id,
                source=source,
                file_name=file_name,
                file_type=file_type,
                metadata={"chunking_method": "semantic"},
            ))
        return self._post_process_chunks(chunks, doc_id, source, file_name, file_type)

    def _split_large_chunk(self, chunk: Chunk, doc_id: str, source: str, file_name: str, file_type: str) -> List[Chunk]:
        """큰 청크 분할 (max_chunk_size 초과 시)"""
        if chunk.char_count <= self._config.max_chunk_size:
            return [chunk]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self._config.max_chunk_size, chunk_overlap=100,
            separators=["\n\n", "\n", ". ", ", ", " "]
        )
        return [Chunk(
            content=t, chunk_id=str(uuid.uuid4()), chunk_index=0,
            doc_id=doc_id, source=source, file_name=file_name, file_type=file_type,
            metadata={**chunk.metadata, "was_split": True}
        ) for t in splitter.split_text(chunk.content)]

    def _merge_small_chunks(self, chunks: List[Chunk], doc_id: str, source: str, file_name: str, file_type: str) -> List[Chunk]:
        """작은 청크 병합 (min_chunk_size 미만 시)"""
        if not chunks:
            return chunks
        min_size, max_size = self._config.min_chunk_size, self._config.max_chunk_size
        merged, buffer = [], ""
        for chunk in chunks:
            combined = buffer + ("\n\n" if buffer else "") + chunk.content
            if chunk.char_count >= min_size and not buffer:
                merged.append(chunk)
            elif len(combined) <= max_size:
                buffer = combined
            else:
                if buffer:
                    merged.append(Chunk(
                        content=buffer, chunk_id=str(uuid.uuid4()), chunk_index=0,
                        doc_id=doc_id, source=source, file_name=file_name, file_type=file_type, metadata={"was_merged": True}
                    ))
                buffer = chunk.content
        if buffer:
            merged.append(Chunk(
                content=buffer, chunk_id=str(uuid.uuid4()), chunk_index=0,
                doc_id=doc_id, source=source, file_name=file_name, file_type=file_type, metadata={}
            ))
        return merged

    def _post_process_chunks(self, chunks: List[Chunk], doc_id: str, source: str, file_name: str, file_type: str) -> List[Chunk]:
        """청크 후처리 (크기 정규화)"""
        split = []
        for c in chunks:
            split.extend(self._split_large_chunk(c, doc_id, source, file_name, file_type))
        merged = self._merge_small_chunks(split, doc_id, source, file_name, file_type)
        for i, c in enumerate(merged):
            c.chunk_index = i
        return merged

    def chunk_document(self, doc: RawDocument) -> List[Chunk]:
        """문서를 청크로 분할"""
        return self.chunk_text(doc.content, str(uuid.uuid4()), doc.source, doc.file_name, doc.file_type)

    def get_chunk_stats(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """청크 통계"""
        if not chunks:
            return {"count": 0}
        sizes = [c.char_count for c in chunks]
        return {"count": len(chunks), "total_chars": sum(sizes), "avg_size": sum(sizes)/len(sizes), "min_size": min(sizes), "max_size": max(sizes)}
