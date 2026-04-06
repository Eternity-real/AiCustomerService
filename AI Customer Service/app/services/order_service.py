from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate, OrderStatus


async def create_order(
    db: AsyncSession,
    user_id: int,
    data: OrderCreate,
) -> Order:
    db_order = Order(
        order_no=data.order_no,
        user_id=user_id,
        items=[item.model_dump(mode="json") for item in data.items],
        total_amount=data.total_amount,
        status=data.status,
        receiver_name=data.receiver_name,
        receiver_phone=data.receiver_phone,
        shipping_address=data.shipping_address,
        remark=data.remark,
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order


async def get_order(
    db: AsyncSession,
    user_id: int,
    order_no: str,
) -> Optional[Order]:
    result = await db.execute(
        select(Order).where(
            Order.order_no == order_no,
            Order.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_orders(
    db: AsyncSession,
    user_id: int,
    status_filter: Optional[OrderStatus],
    skip: int,
    limit: int,
) -> List[Order]:
    query = select(Order).where(Order.user_id == user_id)
    if status_filter is not None:
        query = query.where(Order.status == status_filter)

    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_order(
    db: AsyncSession,
    user_id: int,
    order_no: str,
    data: OrderUpdate,
) -> Optional[Order]:
    result = await db.execute(
        select(Order).where(
            Order.order_no == order_no,
            Order.user_id == user_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    await db.commit()
    await db.refresh(order)
    return order


async def delete_order(
    db: AsyncSession,
    user_id: int,
    order_no: str,
) -> bool:
    result = await db.execute(
        select(Order).where(
            Order.order_no == order_no,
            Order.user_id == user_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        return False

    await db.delete(order)
    await db.commit()
    return True