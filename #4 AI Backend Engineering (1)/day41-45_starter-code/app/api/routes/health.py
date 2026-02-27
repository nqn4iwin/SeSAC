"""
서버 상태 확인 엔드포인트
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> dict:
    """
    기본 헬스체크 엔드포인트
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "lumi-agent",
        "version": "0.5.0",
        "environment": settings.environment,
    }
