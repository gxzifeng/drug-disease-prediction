"""Authentication service layer."""
import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    get_token_expiry_seconds,
    verify_password,
)
from app.models.user import RefreshToken, Role, User
from app.schemas.auth import (
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    Token,
    UserAdminUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
)


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============ User Methods ============
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).options(selectinload(User.roles)).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).options(selectinload(User.roles)).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """Get list of users with pagination."""
        stmt = select(User).options(selectinload(User.roles))
        count_stmt = select(User)
        
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
            count_stmt = count_stmt.where(User.is_active == is_active)
        
        # Get total count
        from sqlalchemy import func
        count_result = await self.db.execute(select(func.count()).select_from(count_stmt.subquery()))
        total = count_result.scalar()
        
        # Get paginated results
        stmt = stmt.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return list(users), total
    
    async def create_user(self, user_data: UserCreate, roles: List[str] = ["user"]) -> User:
        """Create a new user."""
        # Check if username exists
        existing = await self.get_user_by_username(user_data.username)
        if existing:
            raise ValueError("Username already registered")
        
        # Check if email exists
        existing = await self.get_user_by_email(user_data.email)
        if existing:
            raise ValueError("Email already registered")
        
        # Get roles
        role_objs = []
        for role_name in roles:
            role = await self.get_role_by_name(role_name)
            if role:
                role_objs.append(role)
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            roles=role_objs,
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def update_user(self, user: User, user_data: UserUpdate) -> User:
        """Update user profile."""
        update_data = user_data.model_dump(exclude_unset=True)
        
        if "email" in update_data and update_data["email"] != user.email:
            existing = await self.get_user_by_email(update_data["email"])
            if existing:
                raise ValueError("Email already registered")
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def update_user_password(self, user: User, password_data: UserUpdatePassword) -> bool:
        """Update user password."""
        if not verify_password(password_data.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        user.hashed_password = get_password_hash(password_data.new_password)
        user.updated_at = datetime.utcnow()
        await self.db.flush()
        
        return True
    
    async def admin_update_user(self, user: User, user_data: UserAdminUpdate) -> User:
        """Admin update user (including roles)."""
        update_data = user_data.model_dump(exclude_unset=True)
        
        if "email" in update_data and update_data["email"] != user.email:
            existing = await self.get_user_by_email(update_data["email"])
            if existing:
                raise ValueError("Email already registered")
        
        # Handle role update
        if "role_ids" in update_data:
            role_ids = update_data.pop("role_ids")
            if role_ids is not None:
                stmt = select(Role).where(Role.id.in_(role_ids))
                result = await self.db.execute(stmt)
                roles = result.scalars().all()
                user.roles = list(roles)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        await self.db.delete(user)
        await self.db.flush()
        return True
    
    # ============ Authentication Methods ============
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def login(self, username: str, password: str) -> LoginResponse:
        """Login user and return tokens."""
        user = await self.authenticate(username, password)
        if not user:
            raise ValueError("Invalid username or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.flush()
        
        # Create tokens
        token = await self._create_tokens(user)
        
        # Create user response
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=user.role_names,
            created_at=user.created_at,
            last_login=user.last_login,
        )
        
        return LoginResponse(user=user_response, token=token)
    
    async def register(self, user_data: RegisterRequest) -> RegisterResponse:
        """Register a new user."""
        user = await self.create_user(user_data, roles=["user"])
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            roles=user.role_names,
            created_at=user.created_at,
            last_login=user.last_login,
        )
        
        return RegisterResponse(user=user_response)
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        # Check if token is in database and not revoked
        stmt = select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False
        )
        result = await self.db.execute(stmt)
        token_record = result.scalar_one_or_none()
        
        if not token_record or not token_record.is_valid:
            raise ValueError("Refresh token is invalid or expired")
        
        # Get user
        user = await self.get_user_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Revoke old refresh token
        token_record.revoked = True
        
        # Create new tokens
        return await self._create_tokens(user)
    
    async def logout(self, user_id: int, refresh_token: Optional[str] = None) -> bool:
        """Logout user by revoking refresh tokens."""
        if refresh_token:
            # Revoke specific token
            stmt = select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id
            )
            result = await self.db.execute(stmt)
            token_record = result.scalar_one_or_none()
            if token_record:
                token_record.revoked = True
        else:
            # Revoke all tokens for user
            stmt = select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
            result = await self.db.execute(stmt)
            tokens = result.scalars().all()
            for token in tokens:
                token.revoked = True
        
        await self.db.flush()
        return True
    
    async def _create_tokens(self, user: User) -> Token:
        """Create access and refresh tokens for user."""
        # Create access token
        access_token = create_access_token(
            subject=str(user.id),
            roles=user.role_names,
        )
        
        # Create refresh token
        refresh_token_str = create_refresh_token(subject=str(user.id))
        
        # Store refresh token in database
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_record = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=expires_at,
        )
        self.db.add(refresh_token_record)
        await self.db.flush()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=get_token_expiry_seconds(),
        )
    
    # ============ Role Methods ============
    
    async def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        stmt = select(Role).where(Role.id == role_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        stmt = select(Role).where(Role.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_roles(self) -> List[Role]:
        """Get all roles."""
        stmt = select(Role).order_by(Role.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        existing = await self.get_role_by_name(role_data.name)
        if existing:
            raise ValueError("Role already exists")
        
        permissions_str = json.dumps(role_data.permissions) if role_data.permissions else None
        
        role = Role(
            name=role_data.name,
            description=role_data.description,
            permissions=permissions_str,
        )
        
        self.db.add(role)
        await self.db.flush()
        await self.db.refresh(role)
        
        return role
    
    async def update_role(self, role: Role, role_data: RoleUpdate) -> Role:
        """Update a role."""
        update_data = role_data.model_dump(exclude_unset=True)
        
        if "name" in update_data and update_data["name"] != role.name:
            existing = await self.get_role_by_name(update_data["name"])
            if existing:
                raise ValueError("Role name already exists")
        
        if "permissions" in update_data:
            update_data["permissions"] = json.dumps(update_data["permissions"]) if update_data["permissions"] else None
        
        for field, value in update_data.items():
            setattr(role, field, value)
        
        await self.db.flush()
        await self.db.refresh(role)
        
        return role
    
    async def delete_role(self, role_id: int) -> bool:
        """Delete a role."""
        role = await self.get_role_by_id(role_id)
        if not role:
            return False
        
        # Don't allow deleting default roles
        if role.name in ["admin", "user"]:
            raise ValueError("Cannot delete default roles")
        
        await self.db.delete(role)
        await self.db.flush()
        return True
    
    # ============ Initialization Methods ============
    
    async def init_default_roles(self) -> None:
        """Initialize default roles if they don't exist."""
        default_roles = [
            {"name": "admin", "description": "Administrator with full access"},
            {"name": "user", "description": "Regular user with basic access"},
        ]
        
        for role_data in default_roles:
            existing = await self.get_role_by_name(role_data["name"])
            if not existing:
                role = Role(**role_data)
                self.db.add(role)
        
        await self.db.flush()
    
    async def init_superuser(self) -> Optional[User]:
        """Create default superuser if no users exist."""
        # Check if any users exist
        stmt = select(User).limit(1)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return None
        
        # Get admin role
        admin_role = await self.get_role_by_name("admin")
        user_role = await self.get_role_by_name("user")
        
        roles = []
        if admin_role:
            roles.append(admin_role)
        if user_role:
            roles.append(user_role)
        
        # Create superuser
        superuser = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            is_active=True,
            is_superuser=True,
            roles=roles,
        )
        
        self.db.add(superuser)
        await self.db.flush()
        await self.db.refresh(superuser)
        
        return superuser


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse schema."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=user.role_names,
        created_at=user.created_at,
        last_login=user.last_login,
    )


def role_to_response(role: Role) -> RoleResponse:
    """Convert Role model to RoleResponse schema."""
    permissions = json.loads(role.permissions) if role.permissions else None
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=permissions,
        created_at=role.created_at,
    )
