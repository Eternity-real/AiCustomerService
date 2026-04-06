from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..prompts import FAQ_PROMPT, CHAT_PROMPT
from ..utils import call_llm, retrieve_knowledge

async def faq_node(state: AgentState) -> AgentState:
    """FAQ 节点：处理常见问题和闲聊"""
    last_message = state["messages"][-1].content
    intent = state.get("intent", "faq")

    if intent == "chat":
        history_messages = state["messages"][:-1]  # 排除最新消息
        history_text = "\n".join([
            f"{'用户' if isinstance(m, HumanMessage) else '助手'}: {m.content}"
            for m in history_messages[-10:]  # 只取最近 10 条，避免 token 过多
        ])

        prompt = CHAT_PROMPT.format(
            history=history_text,
            user_message=last_message
        )
        response = await call_llm(prompt)
    else:
        context = await retrieve_knowledge(last_message)
        prompt = FAQ_PROMPT.format(context=context, user_question=last_message)
        response = await call_llm(prompt )

    state["final_response"] = response
    return state