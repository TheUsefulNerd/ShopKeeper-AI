"""
Auth tests — 8 cases as specified in the task brief.

Uses FastAPI TestClient (synchronous) against an isolated test database.
Table creation/teardown is handled by the session-scoped fixture in conftest.py.
This module only overrides the get_db dependency to use the test session factory.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.dependencies.auth import get_db
from app.main import app
from config import settings

# ---------------------------------------------------------------------------
# Isolated test DB — overrides the production session factory
# ---------------------------------------------------------------------------

test_engine = create_engine(settings.SUPABASE_TEST_DB_URL)
TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    # Patch Redis blocklist at the route module level — that is where the
    # already-imported names live after `from app.services.auth import ...`.
    # is_refresh_token_blacklisted always returns False (token not revoked).
    # blacklist_refresh_token is a no-op (no Redis needed in tests).
    with (
        patch("app.api.v1.auth.is_refresh_token_blacklisted", return_value=False),
        patch("app.api.v1.auth.blacklist_refresh_token", return_value=None),
    ):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_USER = {"username": "testuser_auth", "password": "securepass123"}


def register(
    client: TestClient,
    username: str = VALID_USER["username"],
    password: str = VALID_USER["password"],
):
    return client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )


def login(
    client: TestClient,
    username: str = VALID_USER["username"],
    password: str = VALID_USER["password"],
):
    return client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_valid_credentials(self, client: TestClient):
        """1 — Register valid credentials → 201."""
        resp = register(client)
        assert resp.status_code == 201
        body = resp.json()
        assert "user_id" in body
        assert body["username"] == VALID_USER["username"]

    def test_register_duplicate_username(self, client: TestClient):
        """2 — Register duplicate username → 400."""
        resp = register(client)  # same user already registered in test above
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_register_password_too_short(self, client: TestClient):
        """3 — Register password under 8 chars → 422."""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "short"},
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_valid_credentials(self, client: TestClient):
        """4 — Login valid credentials → 200 + both tokens."""
        resp = login(client)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        """5 — Login wrong password → 401."""
        resp = login(client, password="wrongpassword")
        assert resp.status_code == 401


class TestProtectedRoute:
    def test_protected_route_with_valid_token(self, client: TestClient):
        """6 — Protected route with valid token → 200."""
        login_resp = login(client)
        token = login_resp.json()["access_token"]
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == VALID_USER["username"]

    def test_protected_route_with_no_token(self, client: TestClient):
        """7 — Protected route with no token → 401."""
        resp = client.get("/api/v1/auth/me")
        # HTTPBearer returns 401 when Authorization header is absent
        assert resp.status_code == 401


class TestRefresh:
    def test_refresh_with_valid_refresh_token(self, client: TestClient):
        """8 — Refresh with valid refresh token → 200 + new access token."""
        login_resp = login(client)
        refresh_token = login_resp.json()["refresh_token"]
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
