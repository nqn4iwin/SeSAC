from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="사용자 메시지",
        examples=["오늘 방송 언제야?", "노래 추천해줘"],
    )

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="세션 식별자",
        examples=["user123", "session-abc-123"],
    )

    user_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="사용자 식별자 (선택)",
    )


class ChatResponse(BaseModel):
    message: str = Field(
        ...,
        description="루미의 응답 메시지",
    )

    tool_used: Optional[str] = Field(
        default=None,
        description="사용된 Tool 이름",
        examples=["get_schedule", "recommend_song", None],
    )

    cached: bool = Field(
        default=False,
        description="캐시된 응답 여부",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="응답 생성 시간 (UTC)",
    )
