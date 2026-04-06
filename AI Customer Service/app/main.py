from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.core.exceptions import register_exception_handlers
from app.api.endpoints.users import router as users_router
from app.api.endpoints.orders import router as orders_router
from app.api.endpoints.tickets import router as tickets_router
from app.api.endpoints.chat import router as chat_router

app = FastAPI()

# 注册全局异常处理器
register_exception_handlers(app)

#注册路由
app.include_router(users_router)
app.include_router(orders_router)
app.include_router(tickets_router)
app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # 前端地址
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,  # 允许携带 cookie
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 头
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
    )