import asyncio
from app.db.database import async_engine
from app.models import Base

async def create_all_tables():
    """异步创建所有数据库表"""
    async with async_engine.begin() as conn:
        # 执行表创建（将 Model 映射为 SQL 并执行）
        await conn.run_sync(Base.metadata.create_all)
        print(Base.metadata.tables)
    print("所有表创建成功！")

if __name__ == "__main__":
    asyncio.run(create_all_tables())