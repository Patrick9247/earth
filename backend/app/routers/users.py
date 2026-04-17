"""
用户管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models import User
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    require_super_admin,
    check_super_admin_key
)

router = APIRouter(prefix="/api/users", tags=["用户管理"])


# ==================== Schemas ====================
class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    super_admin_key: Optional[str] = Field(None, description="超级管理员密钥")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="联系电话")


class UserCreate(BaseModel):
    """超级管理员创建用户"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role: str = Field(default="ADMIN", description="角色: SUPER, ADMIN")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="联系电话")


class UserUpdate(BaseModel):
    """用户更新模型"""
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="新密码")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    is_active: Optional[bool] = Field(None, description="是否启用")


class UserUpdateByAdmin(BaseModel):
    """管理员更新用户模型"""
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="新密码")
    role: Optional[str] = Field(None, description="角色")
    email: Optional[str] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    is_active: Optional[bool] = Field(None, description="是否启用")


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str]
    full_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== API 端点 ====================

@router.post("/register", response_model=UserResponse, summary="用户注册")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    - 普通注册: 不提供 super_admin_key，创建为普通管理员 (ADMIN)
    - 超级管理员注册: 提供正确的 super_admin_key，创建为超级管理员 (SUPER)
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查是否已有超级管理员
    existing_super = db.query(User).filter(User.role == "SUPER").first()
    
    # 确定用户角色
    if user_data.super_admin_key and check_super_admin_key(user_data.super_admin_key):
        role = "SUPER"
    elif existing_super:
        role = "ADMIN"
    else:
        # 第一个注册用户没有密钥，自动成为超级管理员
        role = "SUPER"
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        role=role,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口
    
    返回 JWT 访问令牌
    """
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用，请联系管理员"
        )
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的信息"""
    return current_user


@router.get("/", response_model=List[UserResponse], summary="获取所有用户列表")
def get_users(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（仅超级管理员）"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.get("/{user_id}", response_model=UserResponse, summary="获取指定用户")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户信息"""
    # 普通管理员只能查看自己的信息
    if current_user.role != "SUPER" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该用户信息"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return user


@router.post("/", response_model=UserResponse, summary="创建用户")
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """创建新用户（仅超级管理员）"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 验证角色
    if user_data.role not in ["SUPER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的角色，仅支持 SUPER 或 ADMIN"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
def update_user(
    user_id: int,
    user_data: UserUpdateByAdmin,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 普通管理员只能修改自己的信息，且不能修改自己的角色和启用状态
    if current_user.role != "SUPER":
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改该用户信息"
            )
        # 普通管理员只能修改自己的密码、邮箱、姓名、电话
        if user_data.role is not None or user_data.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改用户角色或启用状态"
            )
    
    # 更新字段
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    if user_data.role:
        user.role = user_data.role
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/{user_id}", response_model=UserResponse, summary="删除用户")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """删除用户（仅超级管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录用户"
        )
    
    db.delete(user)
    db.commit()
    
    return user


@router.patch("/{user_id}/toggle-active", response_model=UserResponse, summary="切换用户启用状态")
def toggle_user_active(
    user_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """切换用户启用状态（仅超级管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能禁用自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改当前登录用户的启用状态"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return user
