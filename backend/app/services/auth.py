"""
Auth service — bcrypt password hashing, JWT issuance/decoding, Redis blocklist,
and Google OAuth 2.0 helpers.

All JWT secrets and Google OAuth credentials come from Pydantic Settings.
Nothing is hardcoded here.
Redis is used to blocklist refresh tokens on logout.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
import redis
from fastapi import HTTPException, status
from jose import JWTError, jwt

from config import settings

# ---------------------------------------------------------------------------
# Redis client — lazily reused across requests
# ---------------------------------------------------------------------------

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.UPSTASH_REDIS_URL, decode_responses=True
        )
    return _redis_client


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plaintext matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _build_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, is_active: bool) -> str:
    """Issue a short-lived access token."""
    return _build_token(
        {"sub": user_id, "is_active": is_active, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Issue a long-lived refresh token."""
    return _build_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_google_pending_token(user_id: str) -> str:
    """
    Issue a short-lived temporary token for the Google OAuth pending state.

    TTL: 15 minutes. Token type: 'google_pending'.
    This token is only accepted by POST /auth/google/complete — it is rejected
    by get_current_user (which only accepts type='access').
    """
    return _build_token(
        {"sub": user_id, "type": "google_pending"},
        timedelta(minutes=15),
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT.

    Raises HTTP 401 if the token is malformed, expired, or missing required fields.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise _CREDENTIALS_EXCEPTION
        return payload
    except JWTError:
        raise _CREDENTIALS_EXCEPTION


# ---------------------------------------------------------------------------
# Refresh token blocklist (Redis)
# ---------------------------------------------------------------------------


def blacklist_refresh_token(token: str) -> None:
    """
    Store the refresh token in Redis with a TTL equal to its remaining lifetime.
    Any subsequent /auth/refresh call with this token will be rejected.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        exp: int | None = payload.get("exp")
        if exp is not None:
            ttl = int(exp - datetime.now(timezone.utc).timestamp())
            if ttl > 0:
                _get_redis().setex(f"blocklist:{token}", ttl, "1")
    except JWTError:
        # Token already invalid — nothing to blocklist
        pass


def is_refresh_token_blacklisted(token: str) -> bool:
    """Return True if the token has been blocklisted via logout."""
    return _get_redis().exists(f"blocklist:{token}") == 1


# ---------------------------------------------------------------------------
# Google OAuth 2.0 helpers
# ---------------------------------------------------------------------------

_GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def build_google_auth_url() -> str:
    """
    Build the redirect URL to Google's OAuth 2.0 consent screen.

    Scopes: openid, email, profile.
    Client ID and redirect URI come from Pydantic Settings.
    """
    import urllib.parse

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    return f"{_GOOGLE_AUTH_BASE}?{urllib.parse.urlencode(params)}"


def exchange_google_code(code: str) -> dict:
    """
    Exchange an authorization code for Google OAuth tokens.

    Returns the token response dict from Google (contains access_token, id_token, etc.).
    Raises HTTP 400 if Google rejects the code.
    """
    response = httpx.post(
        _GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=10.0,
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange Google authorization code",
        )
    return response.json()


def fetch_google_user_info(access_token: str) -> dict:
    """
    Fetch the authenticated user's profile from Google's userinfo endpoint.

    Returns a dict containing at minimum: sub (google_id), email.
    Raises HTTP 400 if the request fails.
    """
    response = httpx.get(
        _GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch Google user info",
        )
    return response.json()
