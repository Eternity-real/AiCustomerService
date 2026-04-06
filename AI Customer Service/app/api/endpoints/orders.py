from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services import order_service
from app.core.response import ApiResponse, success
from app.models.order import Order
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderStatus,
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/", response_model=ApiResponse[OrderResponse])
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[OrderResponse]:
    """
    创建订单（当前登录用户）
    """
    if order_data.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权为其他用户创建订单",
        )

    order = await order_service.create_order(db, current_user.id, order_data)
    return success(data=order)

@router.get("/order-no/{order_no}", response_model=ApiResponse[OrderResponse])
async def get_order(
    order_no: str,  # ← 参数名和类型都改了
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[OrderResponse]:
    """
    根据订单号查询订单详情（当前登录用户）
    """
    order = await order_service.get_order(db, current_user.id, order_no)  # ← 这里也改了
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return success(data=order)


@router.get("/", response_model=ApiResponse[List[OrderResponse]])
async def list_orders(
    status_filter: Optional[OrderStatus] = Query(
        None, alias="status", description="按状态筛选"
    ),
    skip: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[OrderResponse]]:
    """
    分页查询当前用户订单列表
    """
    orders = await order_service.list_orders(
        db=db,
        user_id=current_user.id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )
    return success(data=orders)


@router.put("/order-no/{order_no}", response_model=ApiResponse[OrderResponse])
async def update_order(
    order_no: str,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[OrderResponse]:
    """
    根据订单号更新订单（状态/收货信息/备注）
    """
    order = await order_service.update_order(
        db=db,
        user_id=current_user.id,
        order_no=order_no,  # ← 改为 order_no
        data=order_update,
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return success(data=order)


@router.delete("/order-no/{order_no}", response_model=ApiResponse[bool])
async def delete_order(
    order_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[bool]:
    """
    根据订单号删除订单（物理删除，生产可改为逻辑删除）
    """
    ok = await order_service.delete_order(
        db=db,
        user_id=current_user.id,
        order_no=order_no,  # ← 改为 order_no
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在",
        )
    return success(data=True, message="订单已删除")