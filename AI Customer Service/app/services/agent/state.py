from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.messages import BaseMessage
from sqlalchemy.ext.asyncio import AsyncSession

class AgentState(TypedDict):
    """对话智能体状态"""
    messages: List[BaseMessage]          # 消息历史（包含用户、助手、系统消息）
    user_id: int                         # 当前用户ID
    session_id: int                      # 当前会话ID
    db: AsyncSession                     # 当前请求用的数据库会话
    intent: Optional[str]                # 意图识别结果（如 "query_order", "complaint", "faq"）
    emotion: Optional[Dict[str, Any]]    # 情绪分析结果，如 {"label": "angry", "score": 0.9}
    tool_calls: List[Dict[str, Any]]     # 可选：保留占位，后续如需多工具编排
    handoff_required: bool               # 是否需要转人工
    final_response: Optional[str]          # 最终回复文本