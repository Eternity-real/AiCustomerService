from ..state import AgentState
from ..prompts import INTENT_PROMPT
from ..utils import call_llm

async def intent_node(state: AgentState) -> AgentState:
    """意图识别节点"""
    last_message = state["messages"][-1].content
    history_summary = f"共{len(state['messages'])}条消息"
    prompt = INTENT_PROMPT.format(user_message=last_message, history_summary=history_summary)
    response = await call_llm(prompt)
    intent = response.strip().lower()
    valid_intents = [
        "query_order",
        "create_order",
        "modify_order",
        "delete_order",
        "create_return",
        "create_complaint",
        "faq",
        "chat",
    ]
    if intent not in valid_intents:
        intent = "chat"
    state["intent"] = intent
    return state