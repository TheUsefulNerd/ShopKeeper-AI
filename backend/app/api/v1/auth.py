"""
Auth route handlers.

All routes are under /api/v1/auth/ (prefix applied in main.py).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth import (
    blacklist_refresh_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_refresh_token_blacklisted,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    """
    Register a new user.

    - 201: User created. Returns user_id and username.
    - 400: Username already exists.
    - 422: Validation error (empty username or password < 8 chars).
    """
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(user_id=user.user_id, username=user.username)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate a user and issue access + refresh tokens.

    - 200: Credentials valid. Returns both tokens.
    - 401: Invalid username or password.
    """
    user: User | None = db.query(User).filter(User.username == body.username).first()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.user_id, user.is_active)
    refresh_token = create_refresh_token(user.user_id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(body: RefreshRequest) -> AccessTokenResponse:
    """
    Exchange a valid refresh token for a new access token.

    - 200: Refresh token valid. Returns new access token.
    - 401: Refresh token invalid, expired, or has been logged out.
    """
    token = body.refresh_token

    if is_refresh_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload["sub"]
    is_active: bool = payload.get("is_active", True)

    new_access_token = create_access_token(user_id, is_active)
    return AccessTokenResponse(access_token=new_access_token)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    body: RefreshRequest,
    _current_user: User = Depends(get_current_user),
) -> dict:
    """
    Invalidate the provided refresh token.

    Requires a valid access token in the Authorization header.
    The refresh token is added to a Redis blocklist with a TTL matching its
    remaining lifetime. Any subsequent /auth/refresh with this token returns 401.

    - 200: Token invalidated.
    """
    blacklist_refresh_token(body.refresh_token)
    return {"detail": "Logged out successfully"}


# ---------------------------------------------------------------------------
# GET /auth/me — protected stub for testing the JWT dependency
# ---------------------------------------------------------------------------


@router.get("/me", response_model=RegisterResponse)
def me(current_user: User = Depends(get_current_user)) -> RegisterResponse:
    """
    Return the current authenticated user.

    Used to verify that the JWT dependency works on protected routes.
    """
    return RegisterResponse(user_id=current_user.user_id, username=current_user.username)
