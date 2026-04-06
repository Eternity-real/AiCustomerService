from ..state import AgentState
from ..prompts import HANDOFF_PROMPT
from ..utils import call_llm

async def human_handoff_node(state: AgentState) -> AgentState:
    """转人工节点"""
    state["handoff_required"] = True
    response = await call_llm(HANDOFF_PROMPT)
    state["final_response"] = response
    return state