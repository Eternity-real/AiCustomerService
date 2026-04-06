from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ticket import Ticket
from app.models.order import Order
from app.models.conversation import Session as DBSession
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketStatus


async def create_ticket(
    db: AsyncSession,
    user_id: int,
    data: TicketCreate,
) -> Ticket:
    # 校验关联的订单是否存在且属于当前用户（如果传了）
    if data.order_id is not None:
        result = await db.execute(
            select(Order).where(
                Order.id == data.order_id,
                Order.user_id == user_id,
            )
        )
        order = result.scalar_one_or_none()
        if order is None:
            raise ValueError("关联的订单不存在或不属于当前用户")

    # 校验关联的会话是否存在（如果传了）
    if data.session_id is not None:
        result = await db.execute(
            select(DBSession).where(DBSession.id == data.session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise ValueError("关联的会话不存在")

    db_ticket = Ticket(
        ticket_no=data.ticket_no,
        user_id=user_id,
        order_id=data.order_id,
        session_id=data.session_id,
        type=data.type,
        title=data.title,
        description=data.description,
        status=data.status,
        assigned_to=data.assigned_to,
        resolution=data.resolution,
    )
    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)
    return db_ticket


async def get_ticket(
    db: AsyncSession,
    user_id: int,
    ticket_id: int,
) -> Optional[Ticket]:
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_tickets(
    db: AsyncSession,
    user_id: int,
    status_filter: Optional[TicketStatus],
    skip: int,
    limit: int,
) -> List[Ticket]:
    query = select(Ticket).where(Ticket.user_id == user_id)
    if status_filter is not None:
        query = query.where(Ticket.status == status_filter)

    query = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_ticket(
    db: AsyncSession,
    user_id: int,
    ticket_id: int,
    data: TicketUpdate,
) -> Optional[Ticket]:
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.user_id == user_id,
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    await db.commit()
    await db.refresh(ticket)
    return ticket


async def delete_ticket(
    db: AsyncSession,
    user_id: int,
    ticket_id: int,
) -> bool:
    result = await db.execute(
        select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.user_id == user_id,
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        return False

    await db.delete(ticket)
    await db.commit()
    return True