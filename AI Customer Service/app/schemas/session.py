from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal

SessionStatus = Literal['active', 'closed']

class SessionBase(BaseModel):
    """会话基础信息"""
    user_id: Optional[int] = Field(None, description="关联的用户ID，为空表示未登录会话")
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    status: SessionStatus = Field(default='active', description="会话状态")

class SessionCreate(SessionBase):
    """创建会话请求"""
    session_uuid: str = Field(..., max_length=36, description="会话UUID，全局唯一")

class SessionUpdate(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(None, max_length=200, description="新的会话标题")
    status: Optional[SessionStatus] = Field(None, description="新的会话状态")
    ended_at: Optional[datetime] = Field(None, description="会话结束时间")

class SessionResponse(SessionBase):
    """会话信息响应"""
    id: int = Field(..., description="会话ID")
    session_uuid: str = Field(..., description="会话UUID")
    started_at: datetime = Field(..., description="会话开始时间")
    ended_at: Optional[datetime] = Field(None, description="会话结束时间")
    last_message_at: datetime = Field(..., description="最后消息时间")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )