"""
Auth service — bcrypt password hashing, JWT issuance/decoding, Redis blocklist.

All JWT secrets come from Pydantic Settings. Nothing is hardcoded here.
Redis is used to blocklist refresh tokens on logout.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
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
