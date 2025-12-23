"""
Preprocessing Pipeline Unit Tests

문서 전처리 파이프라인의 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestTextNormalizer:
    """TextNormalizer 테스트"""

    @pytest.fixture
    def normalizer(self, settings):
        """TextNormalizer 인스턴스"""
        from src.infrastructure.preprocessing.normalizer import TextNormalizer
        return TextNormalizer(settings)

    def test_removes_extra_whitespace(self, normalizer):
        """여러 공백을 단일 공백으로 정규화"""
        text = "Hello    World   Test"
        result = normalizer.normalize(text)
        assert "    " not in result
        assert "   " not in result

    def test_removes_extra_newlines(self, normalizer):
        """여러 줄바꿈을 정규화"""
        text = "Line 1\n\n\n\nLine 2\n\n\nLine 3"
        result = normalizer.normalize(text)
        assert "\n\n\n\n" not in result

    def test_preserves_content(self, normalizer):
        """핵심 내용 보존"""
        text = "Important content here"
        result = normalizer.normalize(text)
        assert "Important" in result
        assert "content" in result
        assert "here" in result

    def test_handles_empty_string(self, normalizer):
        """빈 문자열 처리"""
        result = normalizer.normalize("")
        assert result == ""

    def test_handles_whitespace_only(self, normalizer):
        """공백만 있는 문자열 처리"""
        result = normalizer.normalize("   \n\n   ")
        assert result.strip() == ""


class TestChunkingService:
    """ChunkingService 테스트"""

    @pytest.fixture
    def mock_embeddings(self):
        """OpenAIEmbeddings mock"""
        mock = MagicMock()
        mock.embed_documents.return_value = [[0.1] * 1536]
        return mock

    @pytest.fixture
    def mock_semantic_chunker(self):
        """SemanticChunker mock"""
        mock = MagicMock()
        # create_documents returns list of Document-like objects
        mock_doc = MagicMock()
        mock_doc.page_content = "This is a test chunk content."
        mock.create_documents.return_value = [mock_doc]
        return mock

    @pytest.fixture
    def chunking_service(self, settings, mock_embeddings, mock_semantic_chunker):
        """ChunkingService with mocks - directly injecting dependencies"""
        from src.infrastructure.preprocessing.chunking import ChunkingService
        service = ChunkingService(settings)
        # Directly inject mocked dependencies (bypassing lazy init)
        service._embeddings = mock_embeddings
        service._chunker = mock_semantic_chunker
        return service

    def test_chunk_text_returns_list(self, chunking_service):
        """chunk_text가 청크 목록 반환"""
        text = "This is a test document. " * 100
        result = chunking_service.chunk_text(
            text=text,
            doc_id="test-doc-id",
            source="/path/to/test.txt",
            file_name="test.txt",
            file_type="txt"
        )

        assert isinstance(result, list)
        assert len(result) > 0

    def test_chunk_text_returns_chunks_with_content(self, chunking_service):
        """청크가 content 속성 포함"""
        text = "This is a test document."
        result = chunking_service.chunk_text(
            text=text,
            doc_id="test-doc-id",
            source="/path/to/test.txt",
            file_name="test.txt",
            file_type="txt"
        )

        for chunk in result:
            assert hasattr(chunk, 'content')
            assert len(chunk.content) > 0

    def test_chunk_text_preserves_metadata(self, chunking_service):
        """청크가 메타데이터 보존"""
        text = "This is a test document."
        result = chunking_service.chunk_text(
            text=text,
            doc_id="test-doc-id",
            source="/path/to/test.txt",
            file_name="test.txt",
            file_type="txt"
        )

        for chunk in result:
            assert chunk.file_name == "test.txt"
            assert chunk.file_type == "txt"


class TestUnifiedFileParser:
    """UnifiedFileParser 테스트"""

    @pytest.fixture
    def parser(self):
        """UnifiedFileParser 인스턴스"""
        from src.infrastructure.preprocessing.parsers import UnifiedFileParser
        return UnifiedFileParser()

    def test_parse_txt_file(self, parser, tmp_path):
        """TXT 파일 파싱"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello World\nThis is a test.")

        result = parser.parse(str(txt_file))
        assert "Hello World" in result.content
        assert "test" in result.content

    def test_parse_json_file(self, parser, tmp_path):
        """JSON 파일 파싱"""
        import json
        json_file = tmp_path / "test.json"
        data = {"key": "value", "nested": {"inner": "data"}}
        json_file.write_text(json.dumps(data))

        result = parser.parse(str(json_file))
        assert "key" in result.content
        assert "value" in result.content

    def test_parse_unsupported_format_raises_error(self, parser, tmp_path):
        """지원하지 않는 형식은 ValueError 발생"""
        unsupported_file = tmp_path / "test.xyz"
        unsupported_file.write_text("Some content")

        with pytest.raises(ValueError):
            parser.parse(str(unsupported_file))

    def test_get_supported_extensions(self, parser):
        """지원하는 확장자 목록 반환"""
        extensions = parser.get_supported_extensions()
        assert "txt" in extensions
        assert "pdf" in extensions
        assert "json" in extensions


class TestPreprocessingPipeline:
    """PreprocessingPipeline 테스트"""

    @pytest.fixture
    def mock_parser(self):
        """파서 mock"""
        mock = MagicMock()
        raw_doc = MagicMock()
        raw_doc.content = "Test document content. " * 50
        raw_doc.source = "/path/to/test.txt"
        raw_doc.file_name = "test.txt"
        raw_doc.file_type = "txt"
        raw_doc.metadata = {"file_name": "test.txt", "page_number": 1}
        raw_doc.pages = None
        raw_doc.sheets = None
        mock.parse.return_value = raw_doc
        return mock

    @pytest.fixture
    def mock_normalizer(self):
        """정규화기 mock"""
        mock = MagicMock()
        mock.normalize_document.side_effect = lambda x: x  # 입력 그대로 반환
        return mock

    @pytest.fixture
    def mock_chunker(self):
        """청킹 서비스 mock"""
        mock = MagicMock()
        # Create a proper Chunk-like object
        from dataclasses import dataclass
        @dataclass
        class MockChunk:
            content: str = "Chunk content"
            chunk_id: str = "chunk-1"
            chunk_index: int = 0
            doc_id: str = "doc-1"
            source: str = "/path/to/test.txt"
            file_name: str = "test.txt"
            file_type: str = "txt"
            metadata: dict = None
            def __post_init__(self):
                if self.metadata is None:
                    self.metadata = {}
        mock.chunk_document.return_value = [MockChunk()]
        return mock

    @pytest.fixture
    def pipeline(self, settings, mock_parser, mock_normalizer, mock_chunker):
        """PreprocessingPipeline with mocks"""
        from src.infrastructure.preprocessing.pipeline import PreprocessingPipeline
        pipeline = PreprocessingPipeline(settings)
        pipeline._parser = mock_parser
        pipeline._normalizer = mock_normalizer
        # Note: pipeline uses _chunking_service (not _chunking)
        pipeline._chunking_service = mock_chunker
        return pipeline

    def test_process_file_returns_result(self, pipeline):
        """process_file이 PreprocessingResult 반환"""
        result = pipeline.process_file("/path/to/test.txt")

        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'chunks')

    def test_process_file_creates_chunks(self, pipeline, mock_chunker):
        """process_file이 청크 생성"""
        result = pipeline.process_file("/path/to/test.txt")

        assert result.success is True
        assert len(result.chunks) > 0
        mock_chunker.chunk_document.assert_called()

    def test_process_file_handles_parse_failure(self, pipeline, mock_parser):
        """파싱 실패 시 에러 결과"""
        mock_parser.parse.side_effect = ValueError("Unsupported format")

        result = pipeline.process_file("/path/to/unsupported.xyz")

        assert result.success is False
        assert len(result.chunks) == 0
