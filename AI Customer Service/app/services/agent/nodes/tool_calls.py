from ..state import AgentState
from ..prompts import TOOL_RESPONSE_PROMPT
from ..utils import execute_tool, call_llm

async def tool_calls_node(state: AgentState) -> AgentState:
    """工具调用节点：执行意图对应的工具"""
    intent = state["intent"]
    user_id = state["user_id"]
    last_message = state["messages"][-1].content

    # 1. 调用具体业务工具（订单 / 工单等）
    tool_result = await execute_tool(
        intent,
        user_id=user_id,
        last_user_message=last_message,
    )

    # 2. 根据工具结果和情绪，生成自然语言回复
    emotion_label = state.get("emotion", {}).get("label", "neutral")
    prompt = TOOL_RESPONSE_PROMPT.format(
        tool_result=tool_result,
        intent=intent,
        emotion_label=emotion_label,
    )
    response = await call_llm(prompt)
    state["final_response"] = response
    return state