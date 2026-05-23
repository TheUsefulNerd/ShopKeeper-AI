"""
Google OAuth 2.0 tests — 11 cases as specified in the task brief.

Strategy:
- exchange_google_code and fetch_google_user_info are patched at the route
  module level (where they were imported) so no real HTTP calls are made.
- Redis blocklist functions are patched the same way as in test_auth.py.
- Each test class that creates users uses a unique email/username/google_id to
  avoid cross-test pollution within the module-scoped client fixture.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.dependencies.auth import get_db
from app.main import app
from config import settings

# ---------------------------------------------------------------------------
# Isolated test DB (same pattern as test_auth.py)
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


# ---------------------------------------------------------------------------
# Module-scoped client with all external calls patched
# ---------------------------------------------------------------------------

FAKE_GOOGLE_TOKEN = {"access_token": "fake-google-access-token"}
FAKE_USER_INFO_NEW = {"sub": "google-sub-new-001", "email": "newuser@example.com"}
FAKE_USER_INFO_EXISTING = {
    "sub": "google-sub-exist-001",
    "email": "existing@example.com",
}
FAKE_USER_INFO_NO_GOOG_ID = {
    "sub": "google-sub-link-001",
    "email": "nolink@example.com",
}


@pytest.fixture(scope="module")
def client():
    with (
        patch("app.api.v1.auth.is_refresh_token_blacklisted", return_value=False),
        patch("app.api.v1.auth.blacklist_refresh_token", return_value=None),
    ):
        with TestClient(app, follow_redirects=False) as c:
            yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_expired_pending_token(user_id: str) -> str:
    """Issue a google_pending token that expired 1 second ago."""
    payload = {
        "sub": user_id,
        "type": "google_pending",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _make_access_token(user_id: str) -> str:
    """Issue a normal access token (type='access')."""
    payload = {
        "sub": user_id,
        "is_active": True,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# 1. GET /auth/google/initiate → 302 redirect to Google
# ---------------------------------------------------------------------------


class TestGoogleInitiate:
    def test_initiate_returns_302_redirect(self, client: TestClient):
        """1 — GET /auth/google/initiate → 302 with Location pointing to Google."""
        resp = client.get("/api/v1/auth/google/initiate")
        assert resp.status_code == 302
        location = resp.headers["location"]
        assert "accounts.google.com" in location
        assert "openid" in location
        assert "email" in location


# ---------------------------------------------------------------------------
# 2. Callback with new email → 200 + requires_username: true + temp token
# ---------------------------------------------------------------------------


class TestGoogleCallbackNewUser:
    def test_callback_new_email_returns_pending(self, client: TestClient):
        """2 — Callback with new email → GooglePendingResponse."""
        with (
            patch(
                "app.api.v1.auth.exchange_google_code", return_value=FAKE_GOOGLE_TOKEN
            ),
            patch(
                "app.api.v1.auth.fetch_google_user_info",
                return_value=FAKE_USER_INFO_NEW,
            ),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback", params={"code": "fake-code"}
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["requires_username"] is True
        assert "temp_token" in body
        assert body["temp_token"]

        # Verify it's a google_pending token
        payload = jwt.decode(
            body["temp_token"], settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        assert payload["type"] == "google_pending"


# ---------------------------------------------------------------------------
# 3. Callback with existing email → 200 + full JWT issued
# ---------------------------------------------------------------------------


class TestGoogleCallbackExistingUser:
    @pytest.fixture(autouse=True)
    def seed_existing_user(self, client: TestClient):
        """Pre-create a user with the existing email + password."""
        client.post(
            "/api/v1/auth/register",
            json={"username": "existing_oauth_user", "password": "password123"},
        )
        # Set email directly via DB
        db = TestingSessionLocal()
        try:
            from app.models.user import User

            user = db.query(User).filter(User.username == "existing_oauth_user").first()
            if user:
                user.email = FAKE_USER_INFO_EXISTING["email"]
                db.commit()
        finally:
            db.close()

    def test_callback_existing_email_returns_full_jwt(self, client: TestClient):
        """3 — Callback with existing email → TokenResponse with both tokens."""
        with (
            patch(
                "app.api.v1.auth.exchange_google_code", return_value=FAKE_GOOGLE_TOKEN
            ),
            patch(
                "app.api.v1.auth.fetch_google_user_info",
                return_value=FAKE_USER_INFO_EXISTING,
            ),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback", params={"code": "fake-code"}
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        # Confirm it is NOT a pending response
        assert "requires_username" not in body


# ---------------------------------------------------------------------------
# 4. Callback with existing email that has no google_id → google_id gets linked
# ---------------------------------------------------------------------------


class TestGoogleCallbackLinkGoogleId:
    @pytest.fixture(autouse=True)
    def seed_user_without_google_id(self):
        """Pre-create a user with the email but no google_id."""
        db = TestingSessionLocal()
        try:
            from app.models.user import User

            existing = (
                db.query(User)
                .filter(User.email == FAKE_USER_INFO_NO_GOOG_ID["email"])
                .first()
            )
            if existing is None:
                user = User(
                    username="nolink_user",
                    email=FAKE_USER_INFO_NO_GOOG_ID["email"],
                    google_id=None,
                    hashed_password=None,
                    is_active=True,
                )
                db.add(user)
                db.commit()
        finally:
            db.close()

    def test_callback_links_google_id(self, client: TestClient):
        """4 — Callback with email that has no google_id → google_id is linked."""
        with (
            patch(
                "app.api.v1.auth.exchange_google_code", return_value=FAKE_GOOGLE_TOKEN
            ),
            patch(
                "app.api.v1.auth.fetch_google_user_info",
                return_value=FAKE_USER_INFO_NO_GOOG_ID,
            ),
        ):
            resp = client.get(
                "/api/v1/auth/google/callback", params={"code": "fake-code"}
            )

        assert resp.status_code == 200

        # Confirm google_id is now set in the DB
        db = TestingSessionLocal()
        try:
            from app.models.user import User

            user = (
                db.query(User)
                .filter(User.email == FAKE_USER_INFO_NO_GOOG_ID["email"])
                .first()
            )
            assert user is not None
            assert user.google_id == FAKE_USER_INFO_NO_GOOG_ID["sub"]
        finally:
            db.close()


# ---------------------------------------------------------------------------
# 5–9. POST /auth/google/complete
# ---------------------------------------------------------------------------

# Shared: create one pending user for the complete-flow tests
PENDING_EMAIL = "pending_complete@example.com"
PENDING_GOOGLE_SUB = "google-sub-pending-complete"
PENDING_FAKE_USER_INFO = {"sub": PENDING_GOOGLE_SUB, "email": PENDING_EMAIL}


@pytest.fixture(scope="module")
def pending_user_token(client: TestClient):
    """
    Call the callback with a new email to get a google_pending temp_token.
    Returns the temp_token string.
    """
    with (
        patch("app.api.v1.auth.exchange_google_code", return_value=FAKE_GOOGLE_TOKEN),
        patch(
            "app.api.v1.auth.fetch_google_user_info",
            return_value=PENDING_FAKE_USER_INFO,
        ),
    ):
        resp = client.get("/api/v1/auth/google/callback", params={"code": "fake-code"})

    assert resp.status_code == 200
    return resp.json()["temp_token"]


@pytest.fixture(scope="module")
def pending_user_id(pending_user_token: str) -> str:
    """Extract user_id from the pending token payload."""
    payload = jwt.decode(
        pending_user_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    return payload["sub"]


class TestGoogleComplete:
    def test_complete_valid_username_returns_full_jwt(
        self, client: TestClient, pending_user_token: str
    ):
        """5 — /auth/google/complete with valid unique username → 200 + full JWT."""
        resp = client.post(
            "/api/v1/auth/google/complete",
            json={"username": "brandnewuser"},
            headers={"Authorization": f"Bearer {pending_user_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    def test_complete_duplicate_username_returns_400(
        self, client: TestClient, pending_user_token: str
    ):
        """6 — /auth/google/complete with duplicate username → 400."""
        # "brandnewuser" was claimed in test 5 — but that token is spent / user
        # is now active.
        # We need a fresh pending user for this test.
        fresh_email = "pending_dup@example.com"
        fresh_info = {"sub": "google-sub-dup-001", "email": fresh_email}
        with (
            patch(
                "app.api.v1.auth.exchange_google_code", return_value=FAKE_GOOGLE_TOKEN
            ),
            patch("app.api.v1.auth.fetch_google_user_info", return_value=fresh_info),
        ):
            cb_resp = client.get(
                "/api/v1/auth/google/callback", params={"code": "fake-code"}
            )
        fresh_token = cb_resp.json()["temp_token"]

        # "testuser_auth" is registered in test_auth.py's tests (same test DB)
        # Use "existing_oauth_user" which was registered above in this file
        resp = client.post(
            "/api/v1/auth/google/complete",
            json={"username": "existing_oauth_user"},
            headers={"Authorization": f"Bearer {fresh_token}"},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"].lower()

    def test_complete_short_username_returns_422(
        self, client: TestClient, pending_user_token: str
    ):
        """7 — /auth/google/complete with username under 3 chars → 422."""
        # Use a fresh pending user so the token is still valid
        fresh_email = "pending_short@example.com"
        fresh_info = {"sub": "google-sub-short-001", "email": fresh_email}
        with (
            patch(
                "app.api.v1.auth.exchange_google_code", return_value=FAKE_GOOGLE_TOKEN
            ),
            patch("app.api.v1.auth.fetch_google_user_info", return_value=fresh_info),
        ):
            cb_resp = client.get(
                "/api/v1/auth/google/callback", params={"code": "fake-code"}
            )
        fresh_token = cb_resp.json()["temp_token"]

        resp = client.post(
            "/api/v1/auth/google/complete",
            json={"username": "ab"},
            headers={"Authorization": f"Bearer {fresh_token}"},
        )
        assert resp.status_code == 422

    def test_complete_expired_temp_token_returns_401(
        self, client: TestClient, pending_user_id: str
    ):
        """8 — /auth/google/complete with expired temp token → 401."""
        expired_token = _make_expired_pending_token(pending_user_id)
        resp = client.post(
            "/api/v1/auth/google/complete",
            json={"username": "shouldfail"},
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    def test_complete_with_access_token_returns_401(
        self, client: TestClient, pending_user_id: str
    ):
        """9 — /auth/google/complete with regular access token → 401."""
        access_token = _make_access_token(pending_user_id)
        resp = client.post(
            "/api/v1/auth/google/complete",
            json={"username": "shouldalwaysfail"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 401
        assert "google_pending" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 10–11. Login with email or username
# ---------------------------------------------------------------------------


class TestLoginEmailOrUsername:
    @pytest.fixture(autouse=True)
    def seed_user_with_email(self, client: TestClient):
        """Register a fresh user and assign an email directly via DB."""
        client.post(
            "/api/v1/auth/register",
            json={"username": "email_login_user", "password": "emailpass123"},
        )
        db = TestingSessionLocal()
        try:
            from app.models.user import User

            user = db.query(User).filter(User.username == "email_login_user").first()
            if user and user.email is None:
                user.email = "email_login@example.com"
                db.commit()
        finally:
            db.close()

    def test_login_with_email_returns_200(self, client: TestClient):
        """10 — Login with email + password → 200."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "email_login@example.com", "password": "emailpass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_login_with_username_returns_200(self, client: TestClient):
        """11 — Login with username + password → 200 (unchanged behaviour)."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "email_login_user", "password": "emailpass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
