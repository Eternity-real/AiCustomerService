from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLogin
from app.services import auth
from app.api.dependencies import get_current_user
from app.models.user import User
from app.core.response import ApiResponse, success

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=ApiResponse[UserResponse])
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """
    用户注册
    - 检查用户名是否已存在
    - 创建新用户并返回用户信息
    """
    existing_user = await auth.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    new_user = await auth.create_user(db, user_data)
    return success(data=new_user)


@router.post("/login", response_model=ApiResponse[dict])
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[dict]:
    """
    用户登录
    - 验证用户名密码
    - 返回 JWT access token
    """
    user = await auth.get_user_by_username(db, login_data.username)
    if not user or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return success(data={"access_token": access_token, "token_type": "bearer"})


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 兼容的登录端点（用于 Swagger UI Authorize）
    注意：此接口使用 form-data 格式，不是 JSON
    """
    user = await auth.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=ApiResponse[UserResponse])
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> ApiResponse[UserResponse]:
    """
    获取当前登录用户信息
    """
    return success(data=current_user)


@router.put("/me", response_model=ApiResponse[UserResponse])
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApiResponse[UserResponse]:
    """
    修改当前用户资料（目前仅支持修改昵称）
    """
    if user_update.nickname is not None:
        current_user.nickname = user_update.nickname
    # 如果有更多可修改字段，在此处添加
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return success(data=current_user)