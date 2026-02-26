from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.core.config import settings


logger.remove() 
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.debug else "INFO",
    colorize=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("Lumi Agent 서버를 시작합니다...")
    logger.info(f"환경: {settings.environment}")
    logger.info(f"디버그 모드: {settings.debug}")
    logger.info("=" * 50)

    _validate_settings()

    yield  # 이 지점에서 서버가 요청을 처리함

    logger.info("Lumi Agent 서버를 종료합니다...")


def _validate_settings():
    if not settings.upstage_api_key:
        logger.warning("UPSTAGE_API_KEY가 설정되지 않았습니다. LLM 기능을 사용할 수 없습니다.")

    if settings.environment == "production" and settings.debug:
        logger.warning("Production 환경에서 DEBUG 모드가 활성화되어 있습니다!")


app = FastAPI(
    title="Lumi Agent API",
    description="""
    ## 루미(Lumi) - 버추얼 아이돌 AI 에이전트

    팬들의 덕질을 도와주는 AI 에이전트 서비스입니다.

    ### 주요 기능
    - **대화**: 루미와 자연스러운 대화
    - **정보 제공**: 스케줄, 프로필 조회
    - **액션 수행**: 캘린더 등록, 팬레터 저장

    ### 기술 스택
    - LangGraph: 에이전트 워크플로우
    - Upstage Solar: LLM API
    - FastAPI: 웹 프레임워크
    - Supabase: 데이터베이스
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {
        "message": "Lumi Agent API에 오신 것을 환영합니다!",
        "version": "0.1.0",
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
