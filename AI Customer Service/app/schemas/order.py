from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal, List
from decimal import Decimal

OrderStatus = Literal['pending', 'paid', 'shipped', 'completed', 'cancelled']

class OrderItem(BaseModel):
    """订单商品项"""
    name: str = Field(..., max_length=200, description="商品名称")
    quantity: int = Field(..., ge=1, description="购买数量")
    price: Decimal = Field(..., gt=0, description="商品单价")

class OrderBase(BaseModel):
    """订单基础信息"""
    user_id: int = Field(..., description="下单用户ID")
    items: List[OrderItem] = Field(..., description="商品列表")
    total_amount: Decimal = Field(..., gt=0, description="订单总金额")
    status: OrderStatus = Field(default='pending', description="订单状态")
    receiver_name: str = Field(..., max_length=100, description="收货人姓名")
    receiver_phone: str = Field(..., max_length=20, description="收货人电话")
    shipping_address: str = Field(..., description="收货地址")
    remark: Optional[str] = Field(None, description="订单备注")

class OrderCreate(OrderBase):
    """创建订单请求"""
    order_no: str = Field(..., max_length=50, description="订单号，唯一")

class OrderUpdate(BaseModel):
    """更新订单请求"""
    status: Optional[OrderStatus] = Field(None, description="新的订单状态")
    receiver_name: Optional[str] = Field(None, max_length=100, description="新的收货人姓名")
    receiver_phone: Optional[str] = Field(None, max_length=20, description="新的收货人电话")
    shipping_address: Optional[str] = Field(None, description="新的收货地址")
    remark: Optional[str] = Field(None, description="新的订单备注")

class OrderResponse(OrderBase):
    """订单信息响应"""
    id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单号")
    created_at: datetime = Field(..., description="下单时间")
    updated_at: datetime = Field(..., description="订单更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

class OrderInfoExtract(BaseModel):
    """
    从用户消息中提取的订单信息（仅用于 LLM 解析，不直接入库）
    """
    items: List[OrderItem] = Field(..., description="商品列表")
    status: Optional[str] = Field(
        default="pending",
        description="订单状态，可以是中文（如'待付款'）或英文（如'pending'），默认为 pending"
    )
    receiver_name: str = Field(..., max_length=100, description="收货人姓名")
    receiver_phone: str = Field(..., max_length=20, description="收货人电话")
    shipping_address: str = Field(..., description="收货地址")
    remark: Optional[str] = Field(default="", description="备注")