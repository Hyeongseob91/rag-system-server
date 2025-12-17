"""RAG Pipeline - Entry Point"""
from typing import List
from dotenv import load_dotenv

from .config import Settings
from .graph import RAGWorkflow
from .nodes import GeneratorNode, QueryRewriteNode, RetrieverNode, SimpleGeneratorNode
from .schemas.preprocessing import PreprocessingResult
from .services import LLMService, RerankerService, VectorStoreService
from .services.preprocessing import PreprocessingPipeline


class RAGApplication:
    """RAG 애플리케이션 (DI Container)"""

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self._llm_service = LLMService(self.settings)
        self._vectorstore_service = VectorStoreService(self.settings)
        self._reranker_service = RerankerService(self.settings)
        self._preprocessing_pipeline = PreprocessingPipeline(self.settings)

        self._query_rewrite_node = QueryRewriteNode(self._llm_service)
        self._retriever_node = RetrieverNode(self._vectorstore_service, self._reranker_service)
        self._generator_node = GeneratorNode(self._llm_service)
        self._simple_generator_node = SimpleGeneratorNode(self._llm_service)

        self._workflow = RAGWorkflow(
            self._llm_service,
            self._query_rewrite_node,
            self._retriever_node,
            self._generator_node,
            self._simple_generator_node,
        )

    @property
    def vectorstore(self) -> VectorStoreService:
        return self._vectorstore_service

    @property
    def preprocessing(self) -> PreprocessingPipeline:
        return self._preprocessing_pipeline

    def initialize(self, create_collection: bool = False) -> "RAGApplication":
        if self._vectorstore_service.is_ready():
            print("✅ VectorStore 연결 완료")
        else:
            raise RuntimeError("VectorStore 연결 실패")
        if create_collection:
            self._vectorstore_service.create_collection(extended_schema=True)
            print("✅ 컬렉션 생성 완료")
        self._workflow.build()
        print("✅ RAG 워크플로우 빌드 완료")
        return self

    def run(self, question: str) -> str:
        return self._workflow.invoke(question)["final_answer"]

    def ingest_file(self, file_path: str) -> PreprocessingResult:
        result = self._preprocessing_pipeline.process_file(file_path)
        if result.success and result.chunks:
            added = self._vectorstore_service.add_chunks(result.chunks)
            print(f"✅ {result.metadata.file_name}: {added}개 청크 저장")
        return result

    def ingest_directory(self, dir_path: str, recursive: bool = False) -> List[PreprocessingResult]:
        results = self._preprocessing_pipeline.process_directory(dir_path, recursive)
        total = sum(self._vectorstore_service.add_chunks(r.chunks) for r in results if r.success and r.chunks)
        print(f"✅ 총 {total}개 청크 저장")
        return results

    def close(self) -> None:
        self._vectorstore_service.close()
        print("✅ 리소스 정리 완료")


def create_app(settings: Settings = None) -> RAGApplication:
    load_dotenv()
    return RAGApplication(settings)


if __name__ == "__main__":
    load_dotenv()
    app = create_app().initialize()
    print(f"\n질문: RAG 성능 고도화의 개념은?\n")
    print(f"답변:\n{app.run('RAG 성능 고도화의 개념은?')}")
    app.close()
