"""Chunking Service - SemanticChunker"""
import uuid
from typing import Any, Dict, List

from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

from ...config import Settings
from ...schemas.preprocessing import Chunk, RawDocument


class ChunkingService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._config = settings.preprocessing
        self._embeddings = None
        self._chunker = None

    def _initialize(self):
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(model=self._config.embedding_model)
            self._chunker = SemanticChunker(
                embeddings=self._embeddings,
                breakpoint_threshold_type=self._config.breakpoint_type,
                breakpoint_threshold_amount=self._config.breakpoint_threshold,
            )

    def chunk_text(self, text: str, doc_id: str, source: str, file_name: str, file_type: str) -> List[Chunk]:
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
        split = []
        for c in chunks:
            split.extend(self._split_large_chunk(c, doc_id, source, file_name, file_type))
        merged = self._merge_small_chunks(split, doc_id, source, file_name, file_type)
        for i, c in enumerate(merged):
            c.chunk_index = i
        return merged

    def chunk_document(self, doc: RawDocument) -> List[Chunk]:
        return self.chunk_text(doc.content, str(uuid.uuid4()), doc.source, doc.file_name, doc.file_type)

    def get_chunk_stats(self, chunks: List[Chunk]) -> Dict[str, Any]:
        if not chunks:
            return {"count": 0}
        sizes = [c.char_count for c in chunks]
        return {"count": len(chunks), "total_chars": sum(sizes), "avg_size": sum(sizes)/len(sizes), "min_size": min(sizes), "max_size": max(sizes)}
