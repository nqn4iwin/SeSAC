"""
Lumi Agent FastAPI 애플리케이션

이 파일은 FastAPI 애플리케이션의 진입점입니다.
서버 실행, 미들웨어 설정, 라우터 등록 등을 담당합니다.

실행 방법:
    # 개발 서버 (자동 리로드)
    uv run uvicorn app.main:app --reload

    # 프로덕션 서버
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

API 문서:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
"""
from dotenv import load_dotenv
load_dotenv(override=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

import sys

import gradio as gr
from loguru import logger
from app.core.config import settings
from app.api.routes import api_router
from app.graph import get_lumi_graph
from app.ui import create_demo

logger.remove() 
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.debug else "INFO",
    colorize=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리

    FastAPI의 lifespan 이벤트 핸들러입니다.
    서버 시작/종료 시 실행되는 로직을 정의합니다.

    시작 시 (yield 이전):
        - 데이터베이스 연결 설정
        - 캐시 연결 설정
        - LangGraph 그래프 컴파일

    종료 시 (yield 이후):
        - 연결 정리
        - 리소스 해제

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # ===== 서버 시작 시 실행 =====
    logger.info("=" * 50)
    logger.info("Lumi Agent 서버를 시작합니다...")
    logger.info(f"환경: {settings.environment}")
    logger.info(f"디버그 모드: {settings.debug}")
    logger.info("=" * 50)

    _validate_settings()

    try:
        from app.graph import get_lumi_graph
        graph = get_lumi_graph()
        logger.info("LangGraph 그래프 컴파일 완료")
    except Exception as e:
        logger.error(f"LangGraph 초기화 실패")

    yield  # 이 지점에서 서버가 요청을 처리함

    # ===== 서버 종료 시 실행 =====
    logger.info("Lumi Agent 서버를 종료합니다...")


def _validate_settings():
    """
    필수 설정값 검증

    서버 시작 시 필수 환경변수가 설정되어 있는지 확인합니다.
    설정되지 않은 경우 경고 로그를 출력합니다.
    """
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
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ===== CORS 미들웨어 설정 =====
# Cross-Origin Resource Sharing 설정
# 프론트엔드에서 API를 호출할 수 있도록 허용
# 브라우저가 다른 주소(도메인/포트)에 있는 내 서버로 요청을 보낼 수 있게 허락해 주는 문지기 설정

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

gradio_app = create_demo()
app = gr.mount_gradio_app(app, gradio_app, path="/ui")
logger.info("Gradio UI 마운트 완료: /ui")

# FastAPI에서 API 엔드포인트를 정의
    # @app.get : GET 요청을 처리한다. 데이터 조회
    # @app.post : POST 요청을 처리한다. 데이터 생성
    # "/" : URL 경로(Endpoint)를 의미
    # tags : API 문서에서 그룹화할 태그 이름

@app.get("/", tags=["Root"])
def root():
    """
    루트로 접속했을 때(/) -> Gradio가 나오도록 하고 싶다
    """
    return RedirectResponse(url="/ui")

@app.get("/api", tags=["Root"])
async def root() -> dict:
    return {
        "message": "Lumi Agent API에 오신 것을 환영합니다!",
        "version": "0.2.0",
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
        "ui": "/ui",

    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
