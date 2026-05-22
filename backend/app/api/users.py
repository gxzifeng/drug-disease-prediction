"""User management API routes (Admin only)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_superuser, require_admin
from app.models.user import User
from app.schemas.auth import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserAdminUpdate,
    UserCreate,
    UserListResponse,
    UserResponse,
)
from app.schemas.response import PaginatedResponse, ResponseModel
from app.services.auth import AuthService, role_to_response, user_to_response

router = APIRouter(prefix="/users", tags=["User Management"])


# ============ User Management Routes ============

@router.get("", response_model=ResponseModel[PaginatedResponse[UserListResponse]])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (Admin only).
    
    Supports pagination and filtering by active status.
    """
    service = AuthService(db)
    skip = (page - 1) * page_size
    users, total = await service.get_users(skip=skip, limit=page_size, is_active=is_active)
    
    user_list = [
        UserListResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            roles=u.role_names,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]
    
    pages = (total + page_size - 1) // page_size
    
    return ResponseModel(
        data=PaginatedResponse(
            items=user_list,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.post("", response_model=ResponseModel[UserResponse])
async def create_user(
    user_data: UserCreate,
    roles: List[str] = Query(["user"], description="Role names to assign"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user (Admin only).
    
    - **username**: unique username
    - **email**: valid email address
    - **password**: user password
    - **full_name**: optional full name
    - **roles**: list of role names to assign
    """
    try:
        service = AuthService(db)
        user = await service.create_user(user_data, roles=roles)
        user_response = user_to_response(user)
        return ResponseModel(data=user_response, message="User created successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (Admin only).
    """
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_response = user_to_response(user)
    return ResponseModel(data=user_response)


@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user by ID (Admin only).
    
    Can update email, full_name, is_active, is_superuser, and roles.
    """
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent modifying own superuser status
    if user.id == current_user.id and user_data.is_superuser is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own superuser status"
        )
    
    try:
        updated_user = await service.admin_update_user(user, user_data)
        user_response = user_to_response(updated_user)
        return ResponseModel(data=user_response, message="User updated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user by ID (Superuser only).
    
    Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    service = AuthService(db)
    success = await service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return ResponseModel(message="User deleted successfully")


# ============ Role Management Routes ============

@router.get("/roles/list", response_model=ResponseModel[List[RoleResponse]])
async def list_roles(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all roles (Admin only).
    """
    service = AuthService(db)
    roles = await service.get_roles()
    role_list = [role_to_response(r) for r in roles]
    return ResponseModel(data=role_list)


@router.post("/roles", response_model=ResponseModel[RoleResponse])
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new role (Superuser only).
    """
    try:
        service = AuthService(db)
        role = await service.create_role(role_data)
        role_response = role_to_response(role)
        return ResponseModel(data=role_response, message="Role created successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/roles/{role_id}", response_model=ResponseModel[RoleResponse])
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Update role by ID (Superuser only).
    """
    service = AuthService(db)
    role = await service.get_role_by_id(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    try:
        updated_role = await service.update_role(role, role_data)
        role_response = role_to_response(updated_role)
        return ResponseModel(data=role_response, message="Role updated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/roles/{role_id}", response_model=ResponseModel)
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete role by ID (Superuser only).
    
    Cannot delete default roles (admin, user).
    """
    try:
        service = AuthService(db)
        success = await service.delete_role(role_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return ResponseModel(message="Role deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
