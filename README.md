# RAG Pipeline

> Layered Architecture 기반 고성능 RAG(Retrieval-Augmented Generation) 시스템

기업 내부 문서를 기반으로 정확한 답변을 생성하는 AI QA 시스템입니다.
LangGraph 워크플로우 + Hybrid Search(Dense + BM25) + Cross-Encoder Reranking으로 검색 품질을 극대화했습니다.

---

## 핵심 특징

| 기능 | 설명 |
|------|------|
| **Hybrid Search** | Dense Vector + BM25 Sparse Vector를 RRF로 융합 |
| **Cross-Encoder Reranking** | BAAI/bge-reranker-v2-m3로 검색 결과 재정렬 |
| **Semantic Chunking** | 의미 단위로 문서 분할 (LangChain SemanticChunker) |
| **Query Rewriting** | 검색 최적화를 위해 5개 쿼리 변형 생성 |
| **Intelligent Routing** | 검색이 필요한 질문만 RAG 파이프라인 실행 |
| **출처 표기** | 답변 문장별 출처 번호 표기 ([1], [2]) |

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Docker Compose                                    │
│                                                                             │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐    │
│  │             │    │              Backend (FastAPI)                   │    │
│  │   Frontend  │───▶│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │    │
│  │   (React)   │    │  │   API   │──│ Service │──│   LangGraph     │  │    │
│  │   :5173     │◀───│  │ Routes  │  │  Layer  │  │   Workflow      │  │    │
│  │             │    │  └─────────┘  └─────────┘  └─────────────────┘  │    │
│  └─────────────┘    └───────────────────────────────────────────────────┘    │
│                              │                                               │
│         ┌────────────────────┼───────────────────────────────┐              │
│         ▼                    ▼                               ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Qdrant    │    │  Infinity   │    │    Redis    │    │   OpenAI    │  │
│  │  (Vector)   │    │ (Reranker)  │    │   (Cache)   │    │    API      │  │
│  │   :6333     │    │    :8002    │    │    :6379    │    │  (External) │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│  HTTP 요청/응답, DTO 정의                                         │
│  presentation/api/, presentation/dto/                            │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  워크플로우 조합, DI Container                                    │
│  application/container.py, application/workflow.py              │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Domain Layer                              │
│  비즈니스 로직 (Nodes), 도메인 엔티티                             │
│  domain/nodes/, domain/entities/, domain/prompts/               │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                          │
│  외부 시스템 연동 (OpenAI, Qdrant, Infinity)                      │
│  infrastructure/llm_service.py, vectorstore_service.py          │
└─────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Core Layer                               │
│  공통 설정 (Settings)                                            │
│  core/config.py                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Application Layer vs Domain Layer

| 구분 | Application Layer | Domain Layer |
|------|-------------------|--------------|
| **역할** | 노드들을 조합하여 흐름 정의 | 각 노드의 비즈니스 로직 구현 |
| **비유** | 요리 레시피 (순서, 조합) | 개별 요리 기술 (썰기, 볶기) |
| **예시** | RAGWorkflow, RAGApplication | QueryRewriteNode, RetrieverNode |
| **책임** | "무엇을 언제 호출할지" | "호출되면 무엇을 할지" |

```python
# Domain Layer - 단일 책임: 쿼리 재작성만 담당
class QueryRewriteNode(BaseNode):
    def __call__(self, state: RAGState) -> Dict[str, Any]:
        queries = self._llm_service.rewrite(state["question"])
        return {"optimized_queries": queries}

# Application Layer - 노드들을 조합하여 흐름 정의
class RAGWorkflow:
    def build(self):
        workflow = StateGraph(RAGState)
        workflow.add_node("query_rewrite", self._query_rewrite_node)
        workflow.add_node("retriever", self._retriever_node)
        workflow.add_edge("query_rewrite", "retriever")  # 흐름 정의
```

### DI Container (container.py)

여러 기능이 **같은 서비스 인스턴스를 공유**해야 합니다.

```
DI Container가 없다면:
─────────────────────
RAGWorkflow ──→ VectorStoreService #1 ──→ Qdrant 연결 1
UploadAPI ────→ VectorStoreService #2 ──→ Qdrant 연결 2
HealthAPI ────→ VectorStoreService #3 ──→ Qdrant 연결 3

문제: 각 기능마다 새 인스턴스 생성 → 리소스 낭비, 상태 불일치


DI Container가 있다면:
─────────────────────
                   ┌─→ RAGWorkflow.run()
RAGApplication ────┼─→ ingest_file()      ──→ VectorStoreService ──→ Qdrant 연결 1개
(단일 인스턴스)     └─→ API endpoints            (단일 인스턴스)

해결: 서비스 인스턴스 공유, 리소스 효율화, 일관된 상태
```

```python
# application/container.py
class RAGApplication:
    """DI Container - 모든 서비스를 조립하고 관리"""

    def __init__(self, settings: Settings):
        # Infrastructure Layer (한 번만 생성)
        self._llm_service = LLMService(settings)
        self._vectorstore_service = VectorStoreService(settings)

        # Domain Layer (Infrastructure 주입)
        self._query_rewrite_node = QueryRewriteNode(self._llm_service)
        self._retriever_node = RetrieverNode(self._vectorstore_service, ...)

        # Application Layer (Domain 주입)
        self._workflow = RAGWorkflow(...)
```

### DTO vs Entity

| 구분 | DTO (presentation/) | Entity (domain/) |
|------|---------------------|------------------|
| **위치** | Presentation Layer | Domain Layer |
| **용도** | API 통신용 스키마 | 비즈니스 로직용 모델 |
| **예시** | QueryRequest, QueryResponse | Chunk, RewriteResult |
| **변경 이유** | API 스펙 변경 시 | 비즈니스 규칙 변경 시 |

---

## 디렉토리 구조

```
RAG-Pipeline/
├── src/
│   ├── core/                        # 공통 설정
│   │   └── config.py                # Settings
│   │
│   ├── infrastructure/              # 외부 시스템 연동
│   │   ├── llm_service.py           # OpenAI API
│   │   ├── vectorstore_service.py   # Qdrant (Hybrid Search)
│   │   ├── reranker_service.py      # Infinity (Cross-Encoder)
│   │   ├── bm25_service.py          # FastEmbed (Sparse Vector)
│   │   └── preprocessing/           # 문서 전처리
│   │       ├── pipeline.py
│   │       ├── parsers.py
│   │       ├── chunking.py
│   │       └── normalizer.py
│   │
│   ├── domain/                      # 비즈니스 로직
│   │   ├── entities/                # 도메인 엔티티
│   │   │   ├── chunk.py
│   │   │   ├── document.py
│   │   │   └── models.py
│   │   ├── nodes/                   # LangGraph 노드
│   │   │   ├── base.py
│   │   │   ├── query_rewrite.py
│   │   │   ├── retriever.py
│   │   │   ├── generator.py
│   │   │   └── simple_generator.py
│   │   └── prompts/                 # 프롬프트 템플릿
│   │       └── templates.py
│   │
│   ├── application/                 # 유스케이스, 워크플로우
│   │   ├── container.py             # RAGApplication (DI Container)
│   │   ├── workflow.py              # RAGWorkflow (LangGraph)
│   │   └── state.py                 # RAGState
│   │
│   └── presentation/                # HTTP API
│       ├── api/
│       │   ├── main.py              # FastAPI 앱
│       │   ├── dependencies.py      # 의존성 주입
│       │   └── routes/
│       │       ├── query.py
│       │       ├── upload.py
│       │       └── admin.py
│       └── dto/
│           └── schemas.py           # Request/Response
│
├── frontend/                        # React 프론트엔드
├── main.py                          # CLI 진입점
├── Dockerfile
└── docker-compose.yml
```

---

## 기술 스택

### Backend
| 기술 | 용도 |
|------|------|
| Python 3.13 | 런타임 |
| FastAPI | REST API |
| LangGraph | 워크플로우 오케스트레이션 |
| Pydantic | 데이터 검증 |

### AI/ML
| 기술 | 용도 |
|------|------|
| OpenAI GPT-4o | 답변 생성 |
| OpenAI text-embedding-3-small | Dense Vector (1536 dims) |
| FastEmbed Qdrant/bm25 | Sparse Vector (BM25) |
| BAAI/bge-reranker-v2-m3 | Cross-Encoder Reranking |

### Infrastructure
| 기술 | 용도 |
|------|------|
| Qdrant | Vector Database (Hybrid Search) |
| Infinity | Reranker Model Serving (GPU) |
| Redis | 캐싱 |
| Docker Compose | 컨테이너 오케스트레이션 |

---

## Quick Start

```bash
# 1. 환경 변수 설정
cp .env.example .env
echo "OPENAI_API_KEY=sk-..." >> .env

# 2. 전체 스택 시작
docker compose up -d

# 3. 접속
# Frontend: http://localhost:5173
# API Docs: http://localhost:8188/docs
```

---

## RAG 파이프라인 흐름

```
                    ┌─────────┐
                    │  START  │
                    └────┬────┘
                         │
                         ▼
               ┌─────────────────┐
               │  route_question │───────────────┐
               └────────┬────────┘               │
                        │                        │
             vectorstore                       llm
                        │                        │
                        ▼                        ▼
               ┌─────────────────┐      ┌─────────────────┐
               │  query_rewrite  │      │simple_generator │
               └────────┬────────┘      └────────┬────────┘
                        │                        │
                        ▼                        │
               ┌─────────────────┐               │
               │    retriever    │               │
               └────────┬────────┘               │
                        │                        │
                        ▼                        │
               ┌─────────────────┐               │
               │    generator    │               │
               └────────┬────────┘               │
                        │                        │
                        └────────────┬───────────┘
                                     │
                                     ▼
                                 ┌─────┐
                                 │ END │
                                 └─────┘
```

---

## Hybrid Search 메커니즘

```
                    Query: "환불 규정"
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                      ▼
┌─────────────────┐                  ┌─────────────────┐
│  Dense Vector   │                  │  Sparse Vector  │
│   (OpenAI)      │                  │    (BM25)       │
│   1536 dims     │                  │                 │
└────────┬────────┘                  └────────┬────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│  Qdrant Dense   │                  │ Qdrant Sparse   │
│   Top 30 docs   │                  │   Top 30 docs   │
└────────┬────────┘                  └────────┬────────┘
         │                                    │
         └──────────────┬─────────────────────┘
                        ▼
            ┌───────────────────────┐
            │   RRF (Reciprocal     │
            │   Rank Fusion)        │
            └───────────┬───────────┘
                        ▼
            ┌───────────────────────┐
            │  Cross-Encoder        │
            │  Reranking            │
            └───────────┬───────────┘
                        ▼
            ┌───────────────────────┐
            │   Top 5 Documents     │
            └───────────────────────┘
```

---

## API Reference

### POST /api/v1/query

```json
// Request
{ "question": "환불 규정이 어떻게 되나요?" }

// Response
{
  "answer": "환불은 구매 후 7일 이내에 가능합니다. [1]",
  "sources": [{ "content": "환불은 구매 후..." }],
  "processing_time_ms": 2345.67
}
```

### POST /api/v1/upload

```json
// Response
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "document.pdf",
  "status": "pending"
}
```

### GET /api/v1/health

```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "document_count": 150
}
```

---

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | **필수** |
| `QDRANT_HOST` | Qdrant 호스트 | `localhost` |
| `QDRANT_PORT` | Qdrant 포트 | `6333` |
| `RERANKER_BASE_URL` | Infinity Reranker URL | `http://localhost:8002` |

---

## 로컬 개발

```bash
# Python 가상환경
pip install uv
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 인프라만 Docker로 실행
docker compose up -d qdrant redis infinity-reranker

# 백엔드 개발 서버
uvicorn src.presentation.api.main:app --reload --port 8188

# 프론트엔드 개발 서버
cd frontend && npm install && npm run dev
```

---

## License

MIT License
