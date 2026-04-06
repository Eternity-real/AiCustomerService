from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., max_length=50, description="用户名，唯一标识")
    nickname: str = Field(..., max_length=50, description="用户昵称")

class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, description="密码，至少6位")

class UserLogin(BaseModel):
    """用户登陆"""
    username: str = Field(..., max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码，至少6位")

class UserUpdate(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = Field(None, max_length=50, description="新的昵称")

class UserResponse(UserBase):
    """用户信息响应"""
    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="注册时间")
    updated_at: datetime = Field(..., description="信息更新时间")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )