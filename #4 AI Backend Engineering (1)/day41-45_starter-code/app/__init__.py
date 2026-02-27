"""
루미(Lumi) AI 에이전트 - 버추얼 아이돌 어시스턴트

이 패키지는 LangGraph 기반 에이전트를 FastAPI로 서빙하는
Production 수준의 아키텍처를 구현합니다.

구조:
    app/
    ├── api/routes/     # HTTP 엔드포인트
    ├── core/           # 설정, 프롬프트
    └── schemas/        # DTO (Data Transfer Object)
"""

from dotenv import load_dotenv

load_dotenv(override=True)
