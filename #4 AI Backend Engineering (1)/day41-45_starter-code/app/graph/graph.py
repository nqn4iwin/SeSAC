"""
LangGraph 그래프 구성

이 모듈에서 노드와 엣지를 조합하여 완전한 그래프를 구성합니다.
"""

from langgraph.graph import StateGraph, START, END
from loguru import logger

from app.graph.edges import route_by_intent
from app.graph.nodes import router_node, rag_node, tool_node, response_node
from app.graph.state import LumiState
 
_compiled_graph = None

def create_lumi_graph() -> StateGraph:
    logger.info("LangGraph 그래프 생성 시작")

    # Graph 조립
    builder = StateGraph(LumiState)

    # 노드 추가
    builder.add_node("router", router_node)
    builder.add_node("rag", rag_node)
    builder.add_node("tool", tool_node)
    builder.add_node("response", response_node)

    logger.debug("노드 추가 완료: router, rag, tool, response")

    # 엣지 연결
    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        source="router",
        path=route_by_intent,
        path_map={"rag": "rag", "tool": "tool", "response": "response"},
    )
    builder.add_edge("rag", "response")
    builder.add_edge("tool", "response")
    builder.add_edge("response", END)

    # 컴파일
    compiled = builder.compile()

    return compiled

def get_lumi_graph():
    """
    싱글톤 패턴으로 컴파일된 그래프를 반환합니다
    """
    global _compiled_graph

    if _compiled_graph is None:
        _compiled_graph = create_lumi_graph()

    return _compiled_graph