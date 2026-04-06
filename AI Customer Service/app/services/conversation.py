from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.models.conversation import Session as DBSession, Message
from app.services.agent.graph import agent_graph
from app.services.agent.state import AgentState


async def create_session(
    db: AsyncSession,
    user_id: int | None,
    session_uuid: str,
    title: str | None = None,
) -> DBSession:
    db_session = DBSession(
        user_id=user_id,
        session_uuid=session_uuid,
        title=title,
        started_at=datetime.now(timezone.utc),
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


async def add_message(
    db: AsyncSession,
    session_id: int,
    role: str,
    content: str,
    meta_data: Optional[dict] = None,
) -> Message:
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        meta_data=meta_data,
    )
    db.add(msg)

    stmt = (
        update(DBSession)
        .where(DBSession.id == session_id)
        .values(last_message_at=datetime.now(timezone.utc))
    )
    await db.execute(stmt)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_session_messages(
    db: AsyncSession,
    session_id: int,
    limit: int = 50,
    before: int | None = None,
) -> List[Message]:
    query = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
    )
    if before:
        query = query.where(Message.id < before)
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def get_session_by_id_for_user(
    db: AsyncSession,
    session_id: int,
    user_id: int,
) -> Optional[DBSession]:
    result = await db.execute(
        select(DBSession).where(
            DBSession.id == session_id,
            DBSession.user_id == user_id,
        )
    )
    print("===========")
    print(result)
    return result.scalar_one_or_none()


async def list_sessions_for_user(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> List[DBSession]:
    result = await db.execute(
        select(DBSession)
        .where(DBSession.user_id == user_id)
        .order_by(DBSession.last_message_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_session(
    db: AsyncSession,
    user_id: int,
    session_id: int,
    *,
    title: Optional[str] = None,
    status: Optional[str] = None,
    ended_at: Optional[datetime] = None,
) -> Optional[DBSession]:
    session = await get_session_by_id_for_user(db, session_id, user_id)
    if not session:
        return None

    if title is not None:
        session.title = title
    if status is not None:
        session.status = status
    if ended_at is not None:
        session.ended_at = ended_at

    await db.commit()
    await db.refresh(session)
    return session


async def _load_session_messages_asc(
    db: AsyncSession,
    session_id: int,
    limit: int = 50,
) -> List[Message]:
    msgs_desc = await get_session_messages(db, session_id=session_id, limit=limit)
    return list(reversed(msgs_desc))


def _to_lc_messages(msgs: List[Message]) -> List[BaseMessage]:
    lc: List[BaseMessage] = []
    for m in msgs:
        if m.role == "user":
            lc.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc.append(AIMessage(content=m.content))
        else:
            # system：项目里暂时不区分，先当作 user message 处理也能跑通
            lc.append(HumanMessage(content=m.content))
    return lc


async def handle_user_message(
        db: AsyncSession,
        user_id: int,
        content: str,  # ← 用户最新输入
        session_id: Optional[int] = None,
) -> tuple[DBSession, Message]:
    #获取或创建会话
    print("++++++++++++++")
    print(content)
    if session_id is not None:
        session = await get_session_by_id_for_user(db, session_id, user_id)
        if not session:
            raise ValueError("会话不存在或不属于当前用户")
    else:
        new_uuid = str(uuid4())
        title = content[:30]
        session = await create_session(
            db=db,
            user_id=user_id,
            session_uuid=new_uuid,
            title=title,
        )

    #读取历史消息
    history = await _load_session_messages_asc(db, session_id=session.id, limit=10)
    lc_messages = _to_lc_messages(history)
    print("---------------")
    print(history)
    print("---------------")
    print(lc_messages)


    if not lc_messages or lc_messages[-1].content != content:
        # 如果没有历史消息，或者最后一条消息不是当前输入，添加当前输入
        lc_messages.append(HumanMessage(content=content))

    #构造 AgentState
    state: AgentState = {
        "messages": lc_messages,
        "user_id": user_id,
        "session_id": session.id,
        "db": db,
        "intent": None,
        "emotion": None,
        "tool_calls": [],
        "handoff_required": False,
        "final_response": None,
    }

    result_state: AgentState = await agent_graph.ainvoke(state)
    reply_text = result_state.get("final_response") or "抱歉，我暂时无法处理您的请求。"

    # 记录用户消息到数据库
    await add_message(
        db=db,
        session_id=session.id,
        role="user",
        content=content,
        meta_data=None,
    )

    print(result_state.get("intent"))
    print("****************")
    print(result_state.get("tool_calls"))
    print("****************")
    print(result_state.get("messages"))
    print("****************")

    #记录助手消息（可把 intent/emotion 写入 meta_data 便于分析）
    meta = {
        "intent": result_state.get("intent"),
        "emotion": result_state.get("emotion"),
        "handoff_required": result_state.get("handoff_required", False),
    }
    assistant_msg = await add_message(
        db=db,
        session_id=session.id,
        role="assistant",
        content=reply_text,
        meta_data=meta,
    )

    return session, assistant_msg