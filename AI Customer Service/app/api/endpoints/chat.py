from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Message
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    HistoryRequest,
    SessionListItem,
)
from app.schemas.session import SessionResponse, SessionUpdate
from app.schemas.message import MessageResponse
from app.services import conversation
from app.core.response import ApiResponse, success

router = APIRouter(prefix="/api", tags=["聊天会话管理"])


@router.post("/chat/send", response_model=ApiResponse[ChatResponse])
async def send_chat_message(
        data: ChatRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ApiResponse[ChatResponse]:
    """
    发送一条聊天消息：
    - 如果未传 session_id：自动创建新会话
    - 如果传入 session_id：在现有会话中继续对话
    - 返回：会话ID + 助手的回复消息

    功能说明：
    - 智能意图识别（订单查询、创建、修改、删除、退货、投诉、FAQ、闲聊）
    - 情绪识别与安抚性回复
    - 多轮对话上下文记忆
    - RAG 知识库检索（针对商品咨询等专业问题）
    """
    try:
        session, assistant_msg = await conversation.handle_user_message(
            db=db,
            user_id=current_user.id,
            content=data.content,
            session_id=data.session_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # 记录其他异常
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"发送消息失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="消息处理失败，请稍后重试",
        )

    # 让 Pydantic 自动把 SQLAlchemy Message 模型转换成 MessageResponse
    chat_resp = ChatResponse(
        session_id=session.id,
        message=assistant_msg,  # 会被解析为 MessageResponse
    )
    return success(data=chat_resp)


@router.post("/chat/history", response_model=ApiResponse[List[MessageResponse]])
async def get_chat_history(
        data: HistoryRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ApiResponse[List[MessageResponse]]:
    """
    获取会话历史消息（倒序排列，最多返回 limit 条）

    参数说明：
    - session_id: 会话 ID（必填）
    - limit: 返回消息数量上限（默认 50，最大 100）
    - before: 分页游标，指定上一页最后一条消息的 ID，用于加载更多历史消息

    返回：
    - 消息列表（倒序：最新消息在前）
    """
    # 权限校验：会话必须属于当前用户
    session = await conversation.get_session_by_id_for_user(
        db=db,
        session_id=data.session_id,
        user_id=current_user.id,
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或不属于当前用户",
        )

    messages = await conversation.get_session_messages(
        db=db,
        session_id=data.session_id,
        limit=data.limit,
        before=data.before,
    )
    return success(data=messages)


@router.get("/sessions", response_model=ApiResponse[List[SessionListItem]])
async def list_sessions(
        skip: int = Query(0, ge=0, description="分页偏移量"),
        limit: int = Query(20, ge=1, le=100, description="每页数量"),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ApiResponse[List[SessionListItem]]:
    """
    列出当前用户的所有会话（按最后消息时间倒序）

    参数说明：
    - skip: 分页偏移量（默认 0）
    - limit: 每页数量（默认 20，最大 100）

    返回：
    - 会话列表（包含会话 ID、标题、状态、最后消息时间、消息数量）
    """
    sessions = await conversation.list_sessions_for_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    # 统计每个会话的消息数量
    items = []
    for s in sessions:
        # 使用子查询统计消息数量
        msg_count_stmt = (
            select(func.count(Message.id))
            .where(Message.session_id == s.id)
        )
        result = await db.execute(msg_count_stmt)
        message_count = result.scalar() or 0

        items.append(
            SessionListItem(
                id=s.id,
                session_uuid=s.session_uuid,
                title=s.title,
                status=s.status,
                last_message_at=s.last_message_at,
                message_count=message_count,
            )
        )

    return success(data=items)


@router.get("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def get_session(
        session_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ApiResponse[SessionResponse]:
    """
    获取单个会话的详细信息

    参数说明：
    - session_id: 会话 ID

    返回：
    - 会话详细信息（包括标题、状态、开始时间、结束时间、最后消息时间）
    """
    session = await conversation.get_session_by_id_for_user(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或不属于当前用户",
        )
    return success(data=session)


@router.put("/sessions/{session_id}", response_model=ApiResponse[SessionResponse])
async def update_session(
        session_id: int,
        data: SessionUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ApiResponse[SessionResponse]:
    """
    更新会话信息（标题 / 状态 / 结束时间）

    参数说明：
    - session_id: 会话 ID
    - title: 新的会话标题（可选）
    - status: 新的会话状态（active/closed，可选）
    - ended_at: 会话结束时间（可选）

    使用场景：
    - 修改会话标题
    - 手动关闭会话
    - 标记会话已结束
    """
    try:
        session = await conversation.update_session(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            title=data.title,
            status=data.status,
            ended_at=data.ended_at,
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或不属于当前用户",
            )
        return success(data=session)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"更新会话失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新会话失败，请稍后重试",
        )


@router.delete("/sessions/{session_id}", response_model=ApiResponse[dict])
async def delete_session(
        session_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """
    删除会话及其所有消息（软删除或硬删除）

    参数说明：
    - session_id: 会话 ID

    注意事项：
    - 删除会话会同时删除该会话下的所有消息
    - 请谨慎操作，删除后无法恢复
    - 只能删除属于自己的会话
    """
    try:
        session = await conversation.get_session_by_id_for_user(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或不属于当前用户",
            )

        # 删除会话（级联删除所有消息）
        await db.delete(session)
        await db.commit()

        return success(data={"message": "会话已删除", "session_id": session_id})
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"删除会话失败：{e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败，请稍后重试",
        )