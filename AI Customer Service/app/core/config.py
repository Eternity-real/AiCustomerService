from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):

    QIANWEN_APIKEY: str
    PROJECT_NAME: str = "AI Customer Service"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    MODEL_NAME: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    BASE_URL: str

    #RAG相关配置
    RAG_VECTORSTORE_DIR: str
    RAG_EMBEDDING_MODEL: str
    RAG_TOP_K: int
    RAG_ENABLE_SEARCH_TOOL: bool
    RAG_MAX_RECURSION_LIMIT: int
    RAG_RERANK_TOP_N: int
    RAG_SIMILARITY_THRESHOLD: float
    RAG_LLM_MODEL_NAME: Optional[str]  # 若 None 则使用 MODEL_NAME
    RAG_SOURCE_TXT: str  # 知识库源文件路径
    RAG_CHUNK_SIZE: int
    RAG_CHUNK_OVERLAP: int
    SERPAPI_API_KEY: Optional[str]   # 搜索工具 API Key

    model_config = SettingsConfigDict(
        env_file='D:/AI Customer Service/.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
