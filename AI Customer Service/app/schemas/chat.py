from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from .message import MessageResponse

class ChatRequest(BaseModel):
    """发送聊天消息请求"""
    session_id: Optional[int] = Field(None, description="会话ID，为空则创建新会话")
    content: str = Field(..., description="用户消息内容")

class ChatResponse(BaseModel):
    """聊天响应（单条回复）"""
    session_id: int = Field(..., description="会话ID")
    message: MessageResponse = Field(..., description="助手的回复消息")

class HistoryRequest(BaseModel):
    """获取会话历史请求"""
    session_id: int = Field(..., description="会话ID")
    limit: int = Field(default=50, ge=1, le=100, description="返回消息数量上限")
    before: Optional[int] = Field(None, description="分页游标：上一页最后一条消息的ID")

class SessionListItem(BaseModel):
    """会话列表项响应"""
    id: int = Field(..., description="会话ID")
    session_uuid: str = Field(..., description="会话UUID")
    title: Optional[str] = Field(None, description="会话标题")
    status: str = Field(..., description="会话状态")
    last_message_at: datetime = Field(..., description="最后消息时间")
    message_count: Optional[int] = Field(None, description="会话消息总数")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )