"""
AT-001 – Authentication Acceptance Tests
==========================================
Covers PRD acceptance matrix AT-001:

  - POST /api/auth/register  → 201 + token on success
  - POST /api/auth/register  → 400 on duplicate email
  - POST /api/auth/login     → 200 + token on valid credentials
  - POST /api/auth/login     → 401 on wrong password
  - GET  /api/auth/me        → 200 + user profile when authenticated
  - GET  /api/auth/me        → 401 when no token supplied
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

# The `client` fixture is provided by conftest.py


# ── Helpers ─────────────────────────────────────────────────────────────────

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"

VALID_EMAIL = "testuser_at001@example.com"
VALID_PASSWORD = "SecurePass123"


# ── AT-001-1: Registration returns 201 + JWT token ──────────────────────────

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Registering a new user should return HTTP 201 with a valid token payload."""
    resp = await client.post(
        REGISTER_URL,
        json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201, resp.text

    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["email"] == VALID_EMAIL
    assert "user_id" in body
    # Token must be a non-empty string
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 0


# ── AT-001-2: Duplicate registration returns 400 ────────────────────────────

@pytest.mark.asyncio
async def test_register_duplicate_returns_400(client: AsyncClient):
    """Attempting to register the same email twice should return HTTP 400."""
    payload = {"email": "duplicate_at001@example.com", "password": VALID_PASSWORD}
    # First registration must succeed
    first = await client.post(REGISTER_URL, json=payload)
    assert first.status_code == 201, first.text

    # Second registration with the same email must fail
    second = await client.post(REGISTER_URL, json=payload)
    assert second.status_code == 400, second.text

    error_body = second.json()
    # Response should contain an error detail
    assert "detail" in error_body


# ── AT-001-3: Login with correct credentials returns token ───────────────────

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Logging in with valid credentials should return HTTP 200 with a JWT token."""
    # Ensure user exists first
    email = "login_success_at001@example.com"
    await client.post(
        REGISTER_URL,
        json={"email": email, "password": VALID_PASSWORD},
    )

    resp = await client.post(
        LOGIN_URL,
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["email"] == email


# ── AT-001-4: Login with wrong password returns 401 ─────────────────────────

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient):
    """Login with an incorrect password should return HTTP 401."""
    email = "wrong_pass_at001@example.com"
    # Register the user first
    await client.post(
        REGISTER_URL,
        json={"email": email, "password": VALID_PASSWORD},
    )

    resp = await client.post(
        LOGIN_URL,
        json={"email": email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401, resp.text

    error_body = resp.json()
    assert "detail" in error_body


# ── AT-001-5: /me with valid token returns user profile ─────────────────────

@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient):
    """GET /api/auth/me with a valid bearer token should return the user's profile."""
    email = "me_auth_at001@example.com"
    # Register to get a token
    reg = await client.post(
        REGISTER_URL,
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]

    resp = await client.get(
        ME_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["email"] == email
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


# ── AT-001-6: /me without token returns 401 ─────────────────────────────────

@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient):
    """GET /api/auth/me without an Authorization header should return HTTP 401."""
    resp = await client.get(ME_URL)
    assert resp.status_code == 401, resp.text

    error_body = resp.json()
    assert "detail" in error_body
