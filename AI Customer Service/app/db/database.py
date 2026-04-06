from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker,AsyncSession
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
# 创建异步引擎
async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 连接保活
    pool_size=10,
    max_overflow=10,
    echo=False,  # 生产环境关闭 echo，开发可打开看 SQL 日志
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # 异步场景推荐关闭
)
