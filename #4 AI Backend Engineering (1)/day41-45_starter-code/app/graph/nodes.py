# router -> rag -> tool

import json

from pydantic import BaseModel, Field
from langchain_upstage import ChatUpstage
from datetime import datetime
from typing import Literal
from loguru import logger

from app.core.prompts import RESPONSE_PROMPT, ROUTER_PROMPT, RAG_RESPONCE_PROMPT
from app.core.config import settings
from app.graph.state import LumiState
from app.repositories.rag import get_rag_repository
from app.tools.executor import ToolExecutor
from langchain_core.messages import HumanMessage, AIMessage


class RouterOutput(BaseModel):
    """
    라우터 노드의 출력 스키마

    LLM이 JSON 파싱 없이 직접 이 형식으로 응답합니다.
    with_structured_output()을 사용하면 자동으로 파싱됩니다.
    """

    intent: Literal["chat", "rag", "tool"] = Field(
        description="사용자 의도: chat(일반대화), rag(정보검색), tool(도구실행)"
    )
    tool_name: str | None = Field(
        default=None, description="실행할 도구 이름 (intent=tool일 때만)"
    )
    tool_args: dict | None = Field(
        default=None, description="도구 실행 인자 (intent=tool일 때만)"
    )


def get_llm() -> ChatUpstage:
    """
    Upstage Solar LLM 클라이언트를 반환
    """
    return ChatUpstage(
        api_key=settings.upstage_api_key,
        model=settings.llm_model,
        timeout=30,
        max_retries=2,
    )


tool_executor = ToolExecutor()


async def router_node(state: LumiState) -> dict:
    """사용자 의도 분류"""
    logger.info("[Router] 의도 분류 시작")
    last_message = state["messages"][-1]
    user_input = last_message.content

    llm = get_llm()
    structured_llm = llm.with_structured_output(RouterOutput)
    current_date = datetime.now().strftime("%Y-%m-%d")

    messages = [
        HumanMessage(content=f"오늘 날짜: {current_date}\n\n{ROUTER_PROMPT}"),
        HumanMessage(content=f"사용자: {user_input}"),
    ]

    try:
        result = await structured_llm.ainvoke(messages)
        # tool_name 정리
        # LLM은 가끔 예상하지 못한 형식으로 응답
        # 따옴표 포함 -> get_schedule
        # 여러 도구 나열 : "get_schedule, recommend_song"
        # 너무 긴 문자열 : !@#~
        # 방어 로직을 만들어서 안정적인 서비스를 제공
        tool_name = result.tool_name
        if tool_name:
            # 비정상적으로 긴 tool_name 필터링
            if len(tool_name) > 50:
                logger.warning(f"tool_name이 너무 김. ({len(tool_name)}자), 무시")
                tool_name = None
            else:
                # 따옴표를 제거 -> 유니코드 따옴표
                tool_name = tool_name.strip()
                quote_chars = "'\"`'''\"\"「」『』"
                tool_name = tool_name.strip(quote_chars)
                for char in quote_chars:
                    tool_name = tool_name.replace(char, "")

                # 쉼표로 나열된 경우 첫 번째만  사용
                if "," in tool_name:
                    tool_name = tool_name.split(",")[0].strip()
                # tool1?tool2?tool3
                if "?" in tool_name:
                    tool_name = tool_name.split("?")[0].strip()

        # 유효한 Tool 이름만 나오는지 화이트리스트
        valid_tools = [
            "get_schedule",
            "send_fan_letter",
            "recommend_song",
            "get_weather",
        ]

        result_intent = result.intent

        if result_intent == "tool":
            if not tool_name:
                logger.warning("intent=tool인데 tool_name이 없음, chat으로 전환")
                result_intent = "chat"
            elif tool_name not in valid_tools:
                logger.warning(f"유효하지 않은 Tool: {tool_name}, chat으로 전환")
                tool_name = None
                result_intent = "chat"

        logger.debug(
            f"LLM 응답 (structured): intent={result.intent}, "
            f"tool_name={result.tool_name}, tool_args={result.tool_name}"
        )
        logger.info(f"[Router] 의도: {result.intent}, Tool: {result.tool_name}")
        return {
            "intent": result.intent,
            "tool_name": result.tool_name,
            "tool_args": result.tool_args,
        }
    except Exception as e:
        logger.warning(f"Router 노드 오류: {e}, 기본값(chat)으로 설정")
        print(f"Router 오류: {e}")
        return {"intent": "chat", "tool_name": None, "tool_args": None}


async def rag_node(state: LumiState) -> dict:
    """
    RAG 노드 : 관련 문서 검색
    """
    logger.info("[RAG] 문서 검색 시작")

    last_message = state["messages"][-1]
    user_input = last_message.content

    try:
        # RAG에 대한 결과를 가지고 오면 됨
        rag_repo = get_rag_repository()

        docs = await rag_repo.search_similar(
            query=user_input, k=3, filter_status="active"
        )

        # 검색 결과에서 content만 추출
        retrived_docs = [doc["content"] for doc in docs]

        logger.info(f"[RAG] 검색 완료: {len(retrived_docs)}개 문서")

    # 에러를 알려주고 대응
    except Exception as e:
        logger.error(f"[RAG] 검색 실패: {e}")
        retrived_docs = [
            "루미는 프리즘 행성 출신 외계인 공주야",
            "루미의 팬덤은 루미너스야",
        ]

    return {"retrieved_docs": retrived_docs}


async def tool_node(state: LumiState) -> dict:
    """
    Tool 노드: Tool 실행
    LLM이 외부 시스템과 상호작용할 수 있게 해주는 기능
    """
    tool_name = state["tool_name"]
    tool_args = state["tool_args"] or {}

    logger.info(f"[Tool] 실행: {tool_name}, 인자: {tool_args}")

    # 실제로는 DB 조회, API 호출 등을 해야 함
    # Tool 실행을 전담하는 Tool Executor를 만들자

    result = await tool_executor.execute(
        tool_name=tool_name,
        tool_args=tool_args,
        session_id=state["session_id"],
        user_id=state.get("user_id"),
    )

    logger.info(f"[Tool] 실행 결과: {result}")

    return {"tool_result": result}


async def response_node(state: LumiState) -> dict:
    """
    최종 응답 생성

    chat: 일반 대화
    rag: 검색된 문서 기반 응답
    tool: tool 결과 기반 응답
    """
    llm = get_llm()
    user_input = state["messages"][-1].content

    intent = state["intent"]

    if intent == "rag":
        context = "\n".join(state["retrieved_docs"])
        system_prompt = RAG_RESPONCE_PROMPT.format(context=context)

    elif intent == "tool":
        tool_result = state["tool_result"]
        tool_name = state["tool_name"]

        result_context = f"""
        ## 조회 결과 (내부 참고용, 절대 그대로 출력하지 마!)
        tool_name : {tool_name}, tool_result : {json.dumps(tool_result, ensure_ascii=False, indent=2)}
        
        ## 규칙
        - 위 결과를 바탕으로 루미답게 친근하게 안내해줘
        - 성공한 경우: 결과를 자연스럽게 전달 (예: "이번 주 금요일에 뮤직뱅크 나와!")
        - 실패한 경우: 부드럽게 안내 (예: "흠, 지금은 일정이 없나봐!")
        - "get_schedule", "tool", "실행 결과" 같은 기술 용어 절대 금지!
        """
        system_prompt = RESPONSE_PROMPT + result_context

    else:
        system_prompt = RESPONSE_PROMPT

    # 대화 히스토리 관리, 과거 대화를 전달하면 맥락을 이해하면 좋겠음
    history_messages = state["messages"][:-1][-6:] if len(state["messages"]) > 1 else []

    history_text = ""
    if history_messages:
        history_parts = []
        for msg in history_messages:
            role = "사용자" if isinstance(msg, HumanMessage) else "루미"
            history_parts.append(f"{role}: {msg.content}")
        history_text = "\n".join(history_parts)
        history_text = f"\n\n ## 이전 대화: \n{history_text}\n"

    messages = [
        HumanMessage(content=system_prompt + history_text),
        HumanMessage(content=f"사용자: {user_input}"),
    ]

    try:
        response = await llm.ainvoke(messages)
        return {"messages": [AIMessage(content=response.content)]}
    except Exception as e:
        return {
            "messages": [
                AIMessage(content=f"미안, 오류가 생겼어! 다시 말해줄래? ({e})")
            ]
        }
