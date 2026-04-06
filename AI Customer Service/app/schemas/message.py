from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal, Any

MessageRole = Literal['user', 'assistant', 'system']

class MessageBase(BaseModel):
    """消息基础信息"""
    session_id: int = Field(..., description="所属会话ID")
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    meta_data: Optional[dict[str, Any]] = Field(None, description="附加元数据")

class MessageCreate(MessageBase):
    """创建消息请求"""
    pass

class MessageResponse(MessageBase):
    """消息信息响应"""
    id: int = Field(..., description="消息ID")
    created_at: datetime = Field(..., description="消息发送时间")
    updated_at: datetime = Field(..., description="消息更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )