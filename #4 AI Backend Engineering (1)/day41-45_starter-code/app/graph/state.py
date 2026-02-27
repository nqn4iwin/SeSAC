from typing import TypedDict, Literal, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class LumiState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Router 노드에서 결정된 의도
    intent: Literal["chat", "rag", "tool"] | None

    # RAG 노드에서 검색된 문서 내용 목록
    retrieved_docs: list[str]

    # Tool 정보
    tool_name: str | None
    tool_args: dict | None
    tool_result: dict | None

    # 세션
    session_id: str

    # 사용자 식별자
    user_id: str | None


def create_initial_state(
    session_id: str,
    user_id: str | None = None,
    messages: list[BaseMessage] | None = None,
) -> LumiState:
    """
    초기 상태를 설정
    """
    return LumiState(
        messages=messages or [],
        intent=None,
        retrieved_docs=[],
        tool_name=None,
        tool_args=None,
        tool_result=None,
        session_id=session_id,
        user_id=user_id,
    )
