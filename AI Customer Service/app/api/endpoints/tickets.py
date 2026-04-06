from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services import ticket_service
from app.core.response import ApiResponse, success
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketStatus,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("/", response_model=ApiResponse[TicketResponse])
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TicketResponse]:
    """
    创建工单（当前登录用户的反馈 / 投诉）
    """
    if ticket_data.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权为其他用户创建工单",
        )

    try:
        ticket = await ticket_service.create_ticket(
            db=db,
            user_id=current_user.id,
            data=ticket_data,
        )
    except ValueError as e:
        # 关联订单 / 会话不存在等业务错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return success(data=ticket)


@router.get("/{ticket_id}", response_model=ApiResponse[TicketResponse])
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TicketResponse]:
    """
    获取当前用户的某个工单详情
    """
    ticket = await ticket_service.get_ticket(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket_id,
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工单不存在",
        )
    return success(data=ticket)


@router.get("/", response_model=ApiResponse[List[TicketResponse]])
async def list_tickets(
    status_filter: Optional[TicketStatus] = Query(
        None, alias="status", description="按状态筛选"
    ),
    skip: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[TicketResponse]]:
    """
    分页查询当前用户的工单列表
    """
    tickets = await ticket_service.list_tickets(
        db=db,
        user_id=current_user.id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )
    return success(data=tickets)


@router.put("/{ticket_id}", response_model=ApiResponse[TicketResponse])
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[TicketResponse]:
    """
    更新当前用户工单（状态 / 分配人 / 处理结果）
    """
    ticket = await ticket_service.update_ticket(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket_id,
        data=ticket_update,
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工单不存在",
        )
    return success(data=ticket)


@router.delete("/{ticket_id}", response_model=ApiResponse[bool])
async def delete_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[bool]:
    """
    删除当前用户工单（物理删除，生产可改为仅标记关闭）
    """
    ok = await ticket_service.delete_ticket(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket_id,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工单不存在",
        )
    return success(data=True, message="工单已删除")