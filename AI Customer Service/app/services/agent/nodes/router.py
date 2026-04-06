from ..state import AgentState

async def router_node(state: AgentState) -> str:
    """路由节点：根据意图和情绪决定下一个节点"""
    intent = state.get("intent", "other")
    emotion = state.get("emotion", {})

    # 情绪激动（如 angry 分数 > 0.7）直接转人工
    if emotion.get("label") == "angry" and emotion.get("score", 0) > 0.7:
        return "human_handoff"

    # 根据意图路由
    if intent in ["query_order", "create_order", "modify_order", "create_return", "delete_order","create_complaint"]:
        return "tool_calls"

    elif intent == "faq":
        return "faq"

    else:
        return "faq"

