from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal

TicketType = Literal['complaint', 'return', 'exchange', 'other']
TicketStatus = Literal['open', 'processing', 'closed']

class TicketBase(BaseModel):
    """工单基础信息"""
    user_id: int = Field(..., description="提交用户ID")
    order_id: Optional[int] = Field(None, description="关联的订单ID")
    session_id: Optional[int] = Field(None, description="关联的会话ID")
    type: TicketType = Field(..., description="工单类型")
    title: Optional[str] = Field(None, max_length=200, description="工单标题")
    description: str = Field(..., description="详细描述")
    status: TicketStatus = Field(default='open', description="工单状态")
    assigned_to: Optional[str] = Field(None, max_length=50, description="分配给的处理人")
    resolution: Optional[str] = Field(None, description="处理结果")

class TicketCreate(TicketBase):
    """创建工单请求"""
    ticket_no: str = Field(..., max_length=50, description="工单号，唯一")

class TicketUpdate(BaseModel):
    """更新工单请求"""
    status: Optional[TicketStatus] = Field(None, description="新的工单状态")
    assigned_to: Optional[str] = Field(None, max_length=50, description="新的处理人")
    resolution: Optional[str] = Field(None, description="处理结果")

class TicketResponse(TicketBase):
    """工单信息响应"""
    id: int = Field(..., description="工单ID")
    ticket_no: str = Field(..., description="工单号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )