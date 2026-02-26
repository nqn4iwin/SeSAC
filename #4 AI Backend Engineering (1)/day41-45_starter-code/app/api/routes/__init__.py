"""
HTTP 엔드포인트 정의
chat.py : 채팅 API
"""

# FastAPI 라우터 = URL 경로를 정리하는 폴더 구조
# 코드가 많아지면 하나의 파일에 모든 API를 넣을 수 없어서, 도메인별로 파일을 나누고 각 파일에 라우터를 연결

from fastapi import APIRouter
from app.api.routes import chat

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
