# RAG Pipeline

OpenAI API 기반의 고급 RAG(Retrieval-Augmented Generation) 파이프라인입니다.

## 주요 기능

- **LangGraph 기반 워크플로우**: 조건부 라우팅으로 RAG/일반 대화 자동 분기
- **Hybrid Search**: BM25 + Dense Vector 검색
- **CrossEncoder Reranking**: BAAI/bge-reranker-v2-m3 기반
- **Semantic Chunking**: 의미 단위 청킹
- **다중 파일 지원**: PDF, DOCX, XLSX, TXT, JSON
- **REST API**: FastAPI 기반 서빙

## 빠른 시작

### 1. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# OPENAI_API_KEY 설정
nano .env
```

### 2. Docker로 실행

```bash
# 컨테이너 시작
docker compose up -d

# 로그 확인
docker compose logs -f rag-api

# 종료
docker compose down
```

### 3. API 테스트

```bash
# 헬스체크
curl http://localhost:8188/api/v1/health

# 질문하기
curl -X POST http://localhost:8188/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "RAG 시스템의 동작 원리를 설명해주세요."}'
```

## 프로젝트 구조

```
RAG-Pipeline/
├── config/           # 설정 관리
├── schemas/          # 데이터 모델
├── services/         # 비즈니스 로직
│   └── preprocessing/  # 파일 파싱, 청킹
├── nodes/            # LangGraph 노드들
├── graph/            # 워크플로우 정의
├── prompts/          # 프롬프트 템플릿
├── api/              # FastAPI REST API
│   └── routes/
├── main.py           # 진입점
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/` | API 정보 |
| POST | `/api/v1/query` | RAG 질의 |
| POST | `/api/v1/upload` | 파일 업로드 |
| GET | `/api/v1/upload/{task_id}` | 업로드 상태 |
| GET | `/api/v1/health` | 헬스체크 |
| GET | `/api/v1/collections` | 컬렉션 목록 |
| DELETE | `/api/v1/collection/{name}` | 컬렉션 삭제 |
| GET | `/docs` | Swagger UI |

## 로컬 개발

```bash
# 의존성 설치
pip install -e .

# 개발 서버 실행
uvicorn api.main:app --reload --port 8188
```

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 키 | 필수 |
| `WEAVIATE_USE_EMBEDDED` | 임베디드 모드 | `true` |
| `WEAVIATE_HOST` | Weaviate 호스트 | `localhost` |
| `WEAVIATE_PORT` | HTTP 포트 | `8080` |
| `WEAVIATE_GRPC_PORT` | gRPC 포트 | `50051` |
