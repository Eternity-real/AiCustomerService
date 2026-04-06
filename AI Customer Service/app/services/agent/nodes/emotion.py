import json
from ..state import AgentState
from ..prompts import EMOTION_PROMPT
from ..utils import call_llm

async def emotion_node(state: AgentState) -> AgentState:
    """情绪识别节点"""
    last_message = state["messages"][-1].content
    prompt = EMOTION_PROMPT.format(user_message=last_message)
    # 调用千问模型（异步）
    response = await call_llm(prompt)
    try:
        emotion = json.loads(response)
        # 确保包含必要字段
        if "label" not in emotion:
            emotion = {"label": "neutral", "score": 1.0}
    except:
        emotion = {"label": "neutral", "score": 1.0}
    state["emotion"] = emotion
    return state