"""RAG Pipeline API - FastAPI"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .dependencies import lifespan
from .routes import query, upload, admin

app = FastAPI(
    title="RAG Pipeline API",
    description="OpenAI API 기반 RAG 서비스",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(upload.router)
app.include_router(admin.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "InternalServerError", "message": str(exc)})


@app.get("/", tags=["Root"])
async def root():
    return {"service": "RAG Pipeline API", "version": "1.0.0", "docs": "/docs", "health": "/api/v1/health"}
