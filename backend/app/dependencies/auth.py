"""
Reusable JWT validation dependency.

Import get_current_user in any protected route:

    from app.dependencies.auth import get_current_user

    @router.get("/protected")
    def protected(current_user: User = Depends(get_current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth import decode_token

# Use HTTPBearer so the OpenAPI docs show the lock icon on protected routes
_bearer = HTTPBearer()


def get_db() -> Session:  # type: ignore[return]
    """
    Yield a database session.

    Imported here to keep the dependency self-contained.
    The full session factory lives in app/db.py and is used by routes too.
    """
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the Bearer access token and return the authenticated User ORM object.

    Raises HTTP 401 if:
    - Token is missing or malformed
    - Token is expired
    - Token type is not 'access'
    - User not found in the database
    - User account is inactive
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload["sub"]
    user: User | None = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
