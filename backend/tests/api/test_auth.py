"""Tests for authentication API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    """Tests for user registration."""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["user"]["username"] == "newuser"
    
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration with duplicate username."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",  # Same as test_user
                "email": "different@example.com",
                "password": "password123",
            }
        )
        assert response.status_code == 400
    
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "validuser",
                "email": "not-an-email",
                "password": "password123",
            }
        )
        assert response.status_code == 422
    
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with too short password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "validuser",
                "email": "valid@example.com",
                "password": "12345",  # Too short
            }
        )
        assert response.status_code == 422
    
    async def test_register_short_username(self, client: AsyncClient):
        """Test registration with too short username."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "username": "ab",  # Too short
                "email": "valid@example.com",
                "password": "password123",
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """Tests for user login."""
    
    async def test_login_success(self, client: AsyncClient, test_user, db_session):
        """Test successful login."""
        from app.core.security import get_password_hash
        
        # Update test user with proper password hash
        test_user.hashed_password = get_password_hash("testpassword")
        await db_session.commit()
        
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            }
        )
        assert response.status_code == 401
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123",
            }
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestCurrentUser:
    """Tests for current user endpoint."""
    
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current user information."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["username"] == "testuser"
    
    async def test_get_current_user_no_auth(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestRefreshToken:
    """Tests for token refresh endpoint."""
    
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio  
class TestUpdateProfile:
    """Tests for profile update endpoint."""
    
    async def test_update_profile(self, client: AsyncClient, auth_headers):
        """Test updating user profile."""
        response = await client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["full_name"] == "Updated Name"
    
    async def test_update_profile_no_auth(self, client: AsyncClient):
        """Test updating profile without authentication."""
        response = await client.put(
            "/api/v1/auth/me",
            json={"full_name": "New Name"}
        )
        assert response.status_code == 401
