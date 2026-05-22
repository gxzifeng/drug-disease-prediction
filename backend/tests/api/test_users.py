"""Tests for users API endpoints (admin functionality)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Role, UserRole
from app.core.security import get_password_hash


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    # Create admin role
    admin_role = Role(name="admin", description="Administrator")
    db_session.add(admin_role)
    await db_session.flush()
    
    # Create admin user
    admin = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.flush()
    
    # Assign admin role
    user_role = UserRole(user_id=admin.id, role_id=admin_role.id)
    db_session.add(user_role)
    
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def admin_headers(admin_user: User) -> dict:
    """Create auth headers for admin user."""
    from app.core.security import create_access_token
    access_token = create_access_token(data={"sub": admin_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.mark.asyncio
class TestListUsers:
    """Tests for listing users endpoint."""
    
    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test listing users without authentication."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401
    
    async def test_list_users_as_admin(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        """Test listing users as admin."""
        response = await client.get(
            "/api/v1/users",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data["data"]
    
    async def test_list_users_pagination(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test user listing pagination."""
        # Create multiple users
        for i in range(15):
            user = User(
                username=f"listuser{i}",
                email=f"listuser{i}@example.com",
                hashed_password="hashed",
            )
            db_session.add(user)
        await db_session.commit()
        
        response = await client.get(
            "/api/v1/users?page=1&page_size=10",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) <= 10


@pytest.mark.asyncio
class TestGetUser:
    """Tests for getting single user endpoint."""
    
    async def test_get_user_as_admin(
        self, client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """Test getting user details as admin."""
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["username"] == "testuser"
    
    async def test_get_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test getting non-existent user."""
        response = await client.get(
            "/api/v1/users/99999",
            headers=admin_headers,
        )
        assert response.status_code == 404
    
    async def test_get_user_unauthorized(
        self, client: AsyncClient, test_user: User
    ):
        """Test getting user without admin rights."""
        response = await client.get(f"/api/v1/users/{test_user.id}")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateUser:
    """Tests for updating user endpoint."""
    
    async def test_update_user_as_admin(
        self, client: AsyncClient, admin_headers: dict, 
        db_session: AsyncSession, test_user: User
    ):
        """Test updating user as admin."""
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers,
            json={
                "full_name": "Updated Full Name",
                "is_active": True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["full_name"] == "Updated Full Name"
    
    async def test_update_user_unauthorized(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test updating user as non-admin."""
        # Use regular user headers, not admin
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={"full_name": "Hacked Name"}
        )
        # Should be forbidden or not allowed
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
class TestDeleteUser:
    """Tests for deleting user endpoint."""
    
    async def test_delete_user_as_admin(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test deleting user as admin."""
        # Create a user to delete
        user = User(
            username="todelete",
            email="delete@example.com",
            hashed_password="hashed",
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.delete(
            f"/api/v1/users/{user.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
    
    async def test_delete_user_unauthorized(
        self, client: AsyncClient, test_user: User
    ):
        """Test deleting user without admin rights."""
        response = await client.delete(f"/api/v1/users/{test_user.id}")
        assert response.status_code == 401
    
    async def test_delete_self_prevented(
        self, client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        """Test that admin cannot delete themselves."""
        response = await client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers,
        )
        # Should be prevented
        assert response.status_code in [400, 403]


@pytest.mark.asyncio
class TestUserRoles:
    """Tests for user role management."""
    
    async def test_assign_role_to_user(
        self, client: AsyncClient, admin_headers: dict,
        db_session: AsyncSession, test_user: User
    ):
        """Test assigning role to user."""
        # Create a role
        role = Role(name="researcher", description="Researcher role")
        db_session.add(role)
        await db_session.commit()
        
        response = await client.post(
            f"/api/v1/users/{test_user.id}/roles",
            headers=admin_headers,
            json={"role_id": role.id}
        )
        assert response.status_code in [200, 201]
