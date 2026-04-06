from typing import Optional
from mcp.server.fastmcp import FastMCP
from app.db.database import AsyncSessionLocal
from app.schemas.ticket import TicketCreate
from app.services import ticket_service
from app.models.order import Order
from sqlalchemy import select

mcp = FastMCP("ticket-tools")


@mcp.tool(description="创建工单，支持投诉、退货、换货等类型，可关联订单和会话。")
async def ticket_create(
        user_id: int,
        ticket_no: str,
        type: str,
        description: str,
        order_no: Optional[str] = None,
        session_id: Optional[int] = None,
        title: Optional[str] = None,
):
    """创建工单（投诉/退货等）"""
    async with AsyncSessionLocal() as db:
        # 根据订单号查询订单 ID
        order_id = None
        if order_no is not None:
            result = await db.execute(
                select(Order).where(
                    Order.order_no == order_no,
                    Order.user_id == user_id,
                )
            )
            order = result.scalar_one_or_none()
            if order:
                order_id = order.id
            else:
                return {"ok": False, "error": f"订单号 {order_no} 不存在或不属于当前用户"}

        data = TicketCreate(
            ticket_no=ticket_no,
            user_id=user_id,
            order_id=order_id,
            session_id=session_id,
            type=type,
            title=title,
            description=description,
            status="open",
            assigned_to=None,
            resolution=None,
        )
        t = await ticket_service.create_ticket(db=db, user_id=user_id, data=data)
        return {"ok": True, "data": {"id": t.id, "ticket_no": t.ticket_no, "type": t.type, "status": t.status}}


if __name__ == "__main__":
    mcp.run()