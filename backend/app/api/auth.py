"""Authentication API routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    Token,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
)
from app.schemas.response import ResponseModel
from app.services.auth import AuthService, user_to_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ResponseModel[RegisterResponse])
async def register(
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    - **username**: unique username (3-50 characters)
    - **email**: valid email address
    - **password**: password (min 6 characters)
    - **full_name**: optional full name
    """
    try:
        service = AuthService(db)
        result = await service.register(user_data)
        return ResponseModel(data=result, message="Registration successful")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=ResponseModel[LoginResponse])
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.
    
    Returns access token and refresh token.
    """
    try:
        service = AuthService(db)
        result = await service.login(login_data.username, login_data.password)
        return ResponseModel(data=result, message="Login successful")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=ResponseModel[Token])
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Returns new access token and refresh token.
    """
    try:
        service = AuthService(db)
        result = await service.refresh_token(token_data.refresh_token)
        return ResponseModel(data=result, message="Token refreshed successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", response_model=ResponseModel)
async def logout(
    token_data: Optional[RefreshTokenRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by revoking refresh tokens.
    
    If refresh_token is provided, only that token is revoked.
    Otherwise, all refresh tokens for the user are revoked.
    """
    service = AuthService(db)
    refresh_token = token_data.refresh_token if token_data else None
    await service.logout(current_user.id, refresh_token)
    return ResponseModel(message="Logout successful")


@router.get("/me", response_model=ResponseModel[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    user_response = user_to_response(current_user)
    return ResponseModel(data=user_response)


@router.put("/me", response_model=ResponseModel[UserResponse])
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile.
    
    - **email**: new email address
    - **full_name**: new full name
    """
    try:
        service = AuthService(db)
        updated_user = await service.update_user(current_user, user_data)
        user_response = user_to_response(updated_user)
        return ResponseModel(data=user_response, message="Profile updated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/password", response_model=ResponseModel)
async def update_password(
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user password.
    
    - **current_password**: current password for verification
    - **new_password**: new password (min 6 characters)
    """
    try:
        service = AuthService(db)
        await service.update_user_password(current_user, password_data)
        return ResponseModel(message="Password updated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
