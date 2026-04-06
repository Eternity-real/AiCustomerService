from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    异步数据库会话依赖
    每个请求独立会话，请求结束后自动关闭
    """
    async with AsyncSessionLocal() as session:
        yield session