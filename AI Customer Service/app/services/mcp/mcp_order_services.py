from mcp.server.fastmcp import FastMCP
from app.db.database import AsyncSessionLocal
from app.schemas.order import OrderCreate, OrderUpdate
from app.services import order_service
import logging
from typing import Optional

# 配置日志
logger = logging.getLogger(__name__)

mcp = FastMCP("order-tools")


@mcp.tool(description="根据订单号查询单个订单的详细信息，包含商品、金额、收货信息等。")
async def order_get(user_id: int, order_no: str):
    """查询单个订单（按 order_no）"""
    async with AsyncSessionLocal() as db:
        try:
            order = await order_service.get_order(db=db, user_id=user_id, order_no=order_no)
            if not order:
                return {"ok": False, "error": "订单不存在或不属于该用户"}
            return {"ok": True, "data": {
                "id": order.id,
                "order_no": order.order_no,
                "status": order.status,
                "items": order.items,
                "total_amount": float(order.total_amount),
                "receiver_name": order.receiver_name,
                "receiver_phone": order.receiver_phone,
                "shipping_address": order.shipping_address,
                "remark": order.remark,
            }}
        except Exception as e:
            logger.error(f"查询订单失败：{e}", exc_info=True)
            return {"ok": False, "error": f"查询失败：{str(e)}"}


@mcp.tool(description="列出用户的订单，可按状态过滤，支持分页。")
async def order_list(user_id: int, status_filter: Optional[str] = None, skip: int = 0, limit: int = 20):
    """列出订单"""
    async with AsyncSessionLocal() as db:
        try:
            orders = await order_service.list_orders(
                db=db,
                user_id=user_id,
                status_filter=status_filter,
                skip=skip,
                limit=limit,
            )
            return {"ok": True, "data": [
                {"id": o.id, "order_no": o.order_no, "status": o.status, "total_amount": float(o.total_amount)}
                for o in orders
            ]}
        except Exception as e:
            logger.error(f"列出订单失败：{e}", exc_info=True)
            return {"ok": False, "error": f"列出订单失败：{str(e)}"}


@mcp.tool(description="创建新订单，需要提供订单号、商品列表（每个商品包含 name,quantity,price）、总金额、状态、收货信息等。")
async def order_create(
    user_id: int,
    order_no: str,
    items: list,
    total_amount: float,
    status: str,
    receiver_name: str,
    receiver_phone: str,
    shipping_address: str,
    remark: Optional[str] = None,
):
    """创建订单（items 传 list[dict]，字段对齐你的 OrderItem）"""
    async with AsyncSessionLocal() as db:
        try:
            data = OrderCreate(
                order_no=order_no,
                items=items,
                total_amount=total_amount,
                status=status,
                receiver_name=receiver_name,
                receiver_phone=receiver_phone,
                shipping_address=shipping_address,
                remark=remark,
            )
            order = await order_service.create_order(db=db, user_id=user_id, data=data)
            return {"ok": True, "data": {"id": order.id, "order_no": order.order_no, "status": order.status}}
        except Exception as e:
            logger.error(f"创建订单失败：{e}", exc_info=True)
            return {"ok": False, "error": f"创建订单失败：{str(e)}"}


@mcp.tool(description="修改订单的部分信息，如状态、收货人、地址等。")
async def order_update(
        user_id: int,
        order_no: str,
        status: Optional[str] = None,
        receiver_name: Optional[str] = None,
        receiver_phone: Optional[str] = None,
        shipping_address: Optional[str] = None,
        remark: Optional[str] = None,
):
    """修改订单（按 order_no）"""
    async with AsyncSessionLocal() as db:
        try:
            # 构建只包含非 None 字段的字典
            update_data = {}
            if status is not None:
                update_data["status"] = status
            if receiver_name is not None:
                update_data["receiver_name"] = receiver_name
            if receiver_phone is not None:
                update_data["receiver_phone"] = receiver_phone
            if shipping_address is not None:
                update_data["shipping_address"] = shipping_address
            if remark is not None:
                update_data["remark"] = remark

            data = OrderUpdate(**update_data)

            order = await order_service.update_order(
                db=db,
                user_id=user_id,
                order_no=order_no,
                data=data
            )
            if not order:
                return {"ok": False, "error": "订单不存在或不属于该用户"}
            return {"ok": True, "data": {
                "id": order.id,
                "status": order.status,
                "shipping_address": order.shipping_address
            }}
        except Exception as e:
            logger.error(f"修改订单失败：{e}", exc_info=True)
            return {"ok": False, "error": f"修改订单失败：{str(e)}"}

@mcp.tool(description="删除订单（仅当订单属于该用户时有效）。")
async def order_delete(
    user_id: int,
    order_no: str
):
    """删除订单（按 order_no）"""
    async with AsyncSessionLocal() as db:
        try:
            ok = await order_service.delete_order(
                db=db,
                user_id=user_id,
                order_no=order_no
            )
            return {"ok": ok}
        except Exception as e:
            logger.error(f"删除订单失败：{e}", exc_info=True)
            return {"ok": False, "error": f"删除订单失败：{str(e)}"}


if __name__ == "__main__":
    mcp.run()