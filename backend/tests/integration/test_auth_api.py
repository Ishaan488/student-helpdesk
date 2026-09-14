import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, test_admin: dict):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new_student@example.com",
            "password": "strongpassword123",
            "college_id": "REG001",
            "branch": "Computer Science",
            "batch": 2027,
            "cgpa": 8.0,
            "active_backlogs": 0
        },
        headers={"Authorization": f"Bearer {test_admin['token']}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_student@example.com"
    assert data["role"] == "STUDENT"

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: dict, test_admin: dict):
    """Test registration fails if email already exists."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user["user"].email,  # Using the email from the fixture
            "password": "anotherpassword123",
            "college_id": "REG002",
            "branch": "Information Technology",
            "batch": 2027,
            "cgpa": 7.0,
            "active_backlogs": 0
        },
        headers={"Authorization": f"Bearer {test_admin['token']}"}
    )
    assert response.status_code == 400
    assert "A user with this email address already exists." in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: dict):
    """Test successful login with correct credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["user"].email,
            "password": "password123"  # Standard password set in the fixture
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    """Test login fails with incorrect password."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["user"].email,
            "password": "wrongpassword!"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, test_user: dict):
    """Test fetching own profile when authenticated."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["user"].email
    assert data["role"] == "STUDENT"
    assert data["student_profile"]["cgpa"] == 8.5

@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Test fetching profile fails without token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
