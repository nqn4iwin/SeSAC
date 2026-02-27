"""
채팅 API 요청/응답 스키마

이 모듈에서 채팅 관련 API의 데이터 모델을 정의합니다.
2강에서 실제 채팅 API 구현 시 사용됩니다.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, Literal
from datetime import datetime, timezone


class ChatRequest(BaseModel):
    """
    채팅 요청 스키마

    클라이언트에서 서버로 보내는 채팅 메시지 형식입니다.

    Attributes:
        message: 사용자 메시지 내용
        session_id: 세션 식별자 (대화 지속성)
        user_id: 사용자 식별자 (선택)

    Example:
        >>> request = ChatRequest(
        ...     message="오늘 방송 언제야?",
        ...     session_id="user123",
        ... )
    """

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
    """
    채팅 응답 스키마

    서버에서 클라이언트로 보내는 응답 형식입니다.

    Attributes:
        message: 루미의 응답 메시지
        tool_used: 사용된 Tool 이름 (있는 경우)
        cached: 캐시된 응답 여부
        timestamp: 응답 생성 시간

    Example:
        >>> response = ChatResponse(
        ...     message="금요일에 뮤직뱅크 나와!",
        ...     tool_used="get_schedule",
        ... )
    """

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

    # default vs default_factory
    # default : 모든 인스턴스가 같은 값을 공유
    # default_factory : 인스턴스 생성할 때마다 함수를 호출해서 새 값 생성

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="응답 생성 시간 (UTC)",
    )


# 3강 : StreamEvent : SSE 스트리밍 이벤트 스키마
# StreamEventType : SSE 프로토콜에서 이벤트 종류를 구분하기 위한 타입(thinking, tool, token, response, error, done)
# thinking : 노드 진행 상황(루미 생각 중...)
# tool : Tool 실행 결과
# token : LLM 토큰 스트리밍(글자 단위 출력)
# response : 최종 응답 완료
# error : 에러 발생
# done : 스트리밍 종료 신호

StreamEventType = Literal["thinking", "tool", "token", "response", "error", "done"]


class StreamEvent(BaseModel):
    """
    SSE 스트리밍 이벤트 스키마

    각 이벤트 타입에 따라 다른 필드가 채워집니다
    """

    type: StreamEventType = Field(..., description="이벤트 타입")

    # 특정 이벤트는 node 정보가 필수적 ex) thinking
    # done 이벤트는 node가 필수적이지 않음
    # 이렇게 여러 정보를 같이 저장할 때에는 선택적(Optional)
    node: Optional[str] = Field(
        default=None,
        description="현재 실행 중인 노드 이름",
        examples=["router", "rag", "tool", "response"],
    )

    content: Optional[str] = Field(
        default=None, description="텍스트 내용(토큰 또는 최종 응답)"
    )

    tool_name: Optional[str] = Field(
        default=None,
        description="실행된 Tool 이름",
        examples=["get_schedule", "recommend_song"],
    )

    tool_result: Optional[Any] = Field(
        default=None,
        description="Tool 실행 결과",
    )

    tool_used: Optional[str] = Field(
        default=None,
        description="최종 응답에서 사용된 Tool",
    )

    error: Optional[str] = Field(
        default=None,
        description="에러 메시지",
    )

    def to_sse(self) -> str:
        """
        SSE 형식 문자열로 변환
        """
        # 파이썬 표준 json 라이브러리(json) 보다 더 속도가 빠른 라이브러리(orjson)

        import orjson

        # data = {}
        # for k, v in self.model_dump().items():
        #    # SSE 형태로 데이터를 변환, 값이 None인 것은 제외, None이 아닌 것만 데이터를 추가
        #    if v is not None:
        #        data[k] = v
        # 위 형태를 for문이 아니라 dict comprehension으로
        data = {k: v for k, v in self.model_dump().items() if v is not None}
        json_str = orjson.dumps(data).decode("utf-8")
        # dumps가 bytes를 반환해서 decode를 사용해서 반환(문자열) -> SSE로 보내려면 문자열이 필요하기 때문

        return f"data: {json_str}\n\n"


# event = StreamEvent(type="thinking", node="router")
# print("model_dump", event.model_dump())

# print("to_sse", event.to_sse())
