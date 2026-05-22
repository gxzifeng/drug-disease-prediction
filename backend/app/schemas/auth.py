"""Authentication and authorization schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============ Token Schemas ============

class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # user id
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    roles: List[str] = []


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


# ============ User Schemas ============

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserUpdatePassword(BaseModel):
    """Password update schema."""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class UserAdminUpdate(BaseModel):
    """Admin user update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_superuser: bool
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list item response."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ Login Schemas ============

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""
    user: UserResponse
    token: Token


# ============ Role Schemas ============

class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class RoleCreate(RoleBase):
    """Role creation schema."""
    permissions: Optional[List[str]] = None


class RoleUpdate(BaseModel):
    """Role update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    id: int
    permissions: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Registration Schemas ============

class RegisterRequest(UserCreate):
    """Registration request schema."""
    pass


class RegisterResponse(BaseModel):
    """Registration response schema."""
    user: UserResponse
    message: str = "Registration successful"
