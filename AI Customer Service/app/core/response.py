from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar
from fastapi import status

DataT = TypeVar("DataT")

class ApiResponse(BaseModel, Generic[DataT]):
    """通用API响应格式"""
    code: int = status.HTTP_200_OK
    message: str = "Success"
    data: Optional[DataT] = None

def success(data: Any = None, message: str = "Success") -> ApiResponse:
    """成功响应快捷函数"""
    return ApiResponse(code=200, message=message, data=data)

def error(code: int = 400, message: str = "Error", data: Any = None) -> ApiResponse:
    """错误响应快捷函数"""
    return ApiResponse(code=code, message=message, data=data)