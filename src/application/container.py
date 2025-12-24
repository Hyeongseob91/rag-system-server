
"""
RAG Application Container

Application Layer: DI Container 역할을 하는 메인 애플리케이션 클래스
모든 서비스와 노드를 조합하여 RAG 파이프라인을 구성합니다.

왜 Application Layer에 위치하는가?
- "서비스들을 조합해서 유스케이스를 만드는 것"이 Application Layer의 핵심 역할
- Workflow와 함께 애플리케이션의 조립 책임을 담당
- Infrastructure 서비스들을 주입받아 Domain 노드들과 연결
"""
from typing import List
from dotenv import load_dotenv

from src.core import Settings
from src.application.workflow import RAGWorkflow
from src.domain.nodes import GeneratorNode, QueryRewriteNode, RetrieverNode, SimpleGeneratorNode
from src.domain.entities import PreprocessingResult
from src.infrastructure import (
    LLMService,
    RerankerService,
    VectorStoreService,
    CacheService,
    DatabaseService,
    AuthService,
)
from src.infrastructure.repositories import (
    UserRepository,
    ConversationRepository,
    DocumentRepository,
)
from src.infrastructure.preprocessing import PreprocessingPipeline


class RAGApplication:
    """RAG 애플리케이션 (DI Container)

    모든 서비스와 노드를 관리하고 조합합니다.

    왜 DI Container 패턴인가?
    - 서비스 인스턴스를 한 곳에서 관리 (단일 Qdrant 연결 등)
    - 테스트 시 Mock 주입 용이
    - 생명주기 관리 일원화 (initialize, close)

    조립 순서:
    1. Infrastructure Layer (외부 시스템 연결)
    2. Domain Layer (비즈니스 로직 노드)
    3. Application Layer (워크플로우)
    """

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()

        # Infrastructure Layer - 외부 시스템 연결
        self._llm_service = LLMService(self.settings)
        self._vectorstore_service = VectorStoreService(self.settings)
        self._reranker_service = RerankerService(self.settings)
        self._preprocessing_pipeline = PreprocessingPipeline(self.settings)

        # Infrastructure Layer - 캐시, DB, 인증
        self._cache_service = CacheService(self.settings)
        self._database_service = DatabaseService(self.settings)
        self._auth_service = AuthService(self.settings)

        # Infrastructure Layer - Repositories
        self._user_repo = UserRepository(self._database_service)
        self._conversation_repo = ConversationRepository(self._database_service)
        self._document_repo = DocumentRepository(self._database_service)

        # Domain Layer (Nodes) - 비즈니스 로직
        self._query_rewrite_node = QueryRewriteNode(self._llm_service)
        self._retriever_node = RetrieverNode(self._vectorstore_service, self._reranker_service)
        self._generator_node = GeneratorNode(self._llm_service)
        self._simple_generator_node = SimpleGeneratorNode(self._llm_service)

        # Application Layer (Workflow) - 노드 조합
        self._workflow = RAGWorkflow(
            self._llm_service,
            self._query_rewrite_node,
            self._retriever_node,
            self._generator_node,
            self._simple_generator_node,
        )

    # ============ Properties - 기존 서비스 ============

    @property
    def vectorstore(self) -> VectorStoreService:
        """VectorStore 서비스"""
        return self._vectorstore_service

    @property
    def preprocessing(self) -> PreprocessingPipeline:
        """전처리 파이프라인"""
        return self._preprocessing_pipeline

    # ============ Properties - 새 서비스 ============

    @property
    def cache_service(self) -> CacheService:
        """캐시 서비스 (Redis)"""
        return self._cache_service

    @property
    def database_service(self) -> DatabaseService:
        """데이터베이스 서비스 (PostgreSQL)"""
        return self._database_service

    @property
    def auth_service(self) -> AuthService:
        """인증 서비스 (JWT)"""
        return self._auth_service

    @property
    def user_repo(self) -> UserRepository:
        """사용자 Repository"""
        return self._user_repo

    @property
    def conversation_repo(self) -> ConversationRepository:
        """대화 히스토리 Repository"""
        return self._conversation_repo

    @property
    def document_repo(self) -> DocumentRepository:
        """문서 메타데이터 Repository"""
        return self._document_repo

    # ============ Lifecycle ============

    def initialize(self, create_collection: bool = False) -> "RAGApplication":
        """애플리케이션 초기화"""
        # Qdrant 연결 확인
        if self._vectorstore_service.is_ready():
            print("✅ Qdrant 연결 완료")
        else:
            raise RuntimeError("Qdrant 연결 실패")

        if create_collection:
            self._vectorstore_service.create_collection()
            print("✅ 컬렉션 생성 완료 (Dense + BM25 Sparse)")

        # 워크플로우 빌드
        self._workflow.build()
        print("✅ RAG 워크플로우 빌드 완료")

        # Redis 연결 확인 (선택적)
        if self._cache_service.is_ready():
            print("✅ Redis 연결 완료")
        else:
            print("⚠️ Redis 연결 실패 (캐싱 비활성화)")

        # PostgreSQL 연결 확인 및 테이블 생성
        if self._database_service.is_ready():
            self._database_service.create_tables()
            print("✅ PostgreSQL 연결 완료 (테이블 생성)")
        else:
            print("⚠️ PostgreSQL 연결 실패 (DB 기능 비활성화)")

        return self

    def run(self, question: str) -> str:
        """질문에 대한 답변 생성"""
        return self._workflow.invoke(question)["final_answer"]

    def ingest_file(self, file_path: str) -> PreprocessingResult:
        """파일 수집 (전처리 → 벡터 저장)"""
        result = self._preprocessing_pipeline.process_file(file_path)
        if result.success and result.chunks:
            added = self._vectorstore_service.add_chunks(result.chunks)
            print(f"✅ {result.metadata.file_name}: {added}개 청크 저장")
        return result

    def ingest_directory(self, dir_path: str, recursive: bool = False) -> List[PreprocessingResult]:
        """디렉토리 일괄 수집"""
        results = self._preprocessing_pipeline.process_directory(dir_path, recursive)
        total = sum(self._vectorstore_service.add_chunks(r.chunks) for r in results if r.success and r.chunks)
        print(f"✅ 총 {total}개 청크 저장")
        return results

    def close(self) -> None:
        """리소스 정리"""
        self._vectorstore_service.close()
        self._reranker_service.close()
        self._cache_service.close()
        self._database_service.close()
        print("✅ 리소스 정리 완료")


def create_app(settings: Settings = None) -> RAGApplication:
    """애플리케이션 팩토리"""
    load_dotenv()
    return RAGApplication(settings)
