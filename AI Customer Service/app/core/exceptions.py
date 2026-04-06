import traceback
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from .response import error

# 配置日志（可根据项目实际日志配置调整）
logger = logging.getLogger(__name__)

class BusinessError(Exception):
    """业务逻辑异常，可携带自定义状态码和消息"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)

def register_exception_handlers(app):
    """注册全局异常处理器到 FastAPI 应用"""

    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        logger.warning(f"Business error: {exc.message}")
        return JSONResponse(
            status_code=exc.code,
            content=error(code=exc.code, message=exc.message).model_dump()
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # 处理 FastAPI 内置的 HTTPException
        logger.warning(f"HTTP exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content=error(code=exc.status_code, message=exc.detail).model_dump()
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        # 数据库完整性错误（如唯一约束冲突）
        logger.error(f"Database integrity error: {exc}")
        logger.debug(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error(
                code=status.HTTP_400_BAD_REQUEST,
                message="数据冲突，操作无法完成（可能重复或违反约束）"
            ).model_dump()
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        # 其他数据库错误
        logger.error(f"Database error: {exc}")
        logger.debug(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="数据库操作失败"
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        # 未捕获的异常（生产环境应避免暴露细节）
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="内部服务器错误"
            ).model_dump()
        )