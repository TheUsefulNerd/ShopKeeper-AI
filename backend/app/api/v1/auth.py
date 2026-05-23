"""
Auth route handlers.

All routes are under /api/v1/auth/ (prefix applied in main.py).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    CompleteGoogleRegistrationRequest,
    GooglePendingResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services.auth import (
    blacklist_refresh_token,
    build_google_auth_url,
    create_access_token,
    create_google_pending_token,
    create_refresh_token,
    decode_token,
    exchange_google_code,
    fetch_google_user_info,
    hash_password,
    is_refresh_token_blacklisted,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Bearer extractor reused by /google/complete (does not go through get_current_user)
_bearer = HTTPBearer()


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
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

    The 'username' field accepts either a username or an email address.
    If the value contains '@' it is treated as an email, otherwise as a username.

    - 200: Credentials valid. Returns both tokens.
    - 401: Invalid credentials or account has no password (OAuth-only user).
    """
    identifier = body.username  # field name preserved for backward compat

    if "@" in identifier:
        user: User | None = db.query(User).filter(User.email == identifier).first()
    else:
        user = db.query(User).filter(User.username == identifier).first()

    # Reject if user not found, no password set (OAuth-only), or wrong password
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(body.password, user.hashed_password)
    ):
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
    return RegisterResponse(
        user_id=current_user.user_id,
        username=current_user.username,
    )


# ---------------------------------------------------------------------------
# GET /auth/google/initiate
# ---------------------------------------------------------------------------


@router.get("/google/initiate", status_code=status.HTTP_302_FOUND)
def google_initiate() -> RedirectResponse:
    """
    Redirect the user to Google's OAuth 2.0 consent screen.

    Scopes: openid, email, profile.
    Client ID and redirect URI come from Pydantic Settings — never hardcoded.

    - 302: Redirects to Google consent screen.
    """
    url = build_google_auth_url()
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


# ---------------------------------------------------------------------------
# GET /auth/google/callback
# ---------------------------------------------------------------------------


@router.get(
    "/google/callback",
    response_model=TokenResponse | GooglePendingResponse,
)
def google_callback(
    code: str,
    db: Session = Depends(get_db),
) -> TokenResponse | GooglePendingResponse:
    """
    Handle Google's OAuth 2.0 callback.

    Exchanges the authorization code for tokens, fetches the user's Google profile,
    then either:
    - Existing email in DB → link google_id if missing → issue full JWT → TokenResponse
    - New email → create partial User (no username, is_active=False) →
      issue 15-min google_pending token → GooglePendingResponse

    - 200: Returns TokenResponse (existing user) or GooglePendingResponse (new user).
    - 400: Google code exchange or userinfo fetch failed.
    """
    token_data = exchange_google_code(code)
    google_access_token: str = token_data["access_token"]

    user_info = fetch_google_user_info(google_access_token)
    email: str = user_info["email"]
    google_id: str = user_info["sub"]

    user: User | None = db.query(User).filter(User.email == email).first()

    if user is not None:
        # Existing user — link google_id if this is their first OAuth login
        if user.google_id is None:
            user.google_id = google_id
            db.commit()
            db.refresh(user)

        access_token = create_access_token(user.user_id, user.is_active)
        refresh_token = create_refresh_token(user.user_id)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    # New user — create partial record and return pending response
    partial_user = User(
        email=email,
        google_id=google_id,
        is_active=False,
    )
    db.add(partial_user)
    db.commit()
    db.refresh(partial_user)

    temp_token = create_google_pending_token(partial_user.user_id)
    return GooglePendingResponse(temp_token=temp_token)


# ---------------------------------------------------------------------------
# POST /auth/google/complete
# ---------------------------------------------------------------------------


@router.post("/google/complete", response_model=TokenResponse)
def google_complete(
    body: CompleteGoogleRegistrationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Complete Google OAuth registration by setting a username.

    Protected by a google_pending token only (type must be 'google_pending').
    Regular access tokens are rejected.

    - 200: Username set, account activated. Returns full JWT.
    - 400: Username already taken.
    - 401: Token missing, expired, invalid, or wrong type.
    - 422: Username under 3 chars or empty.
    """
    token = credentials.credentials
    payload = decode_token(token)  # raises 401 if invalid/expired

    if payload.get("type") != "google_pending":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — google_pending token required",
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

    # Check username uniqueness
    taken = db.query(User).filter(User.username == body.username).first()
    if taken is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    user.username = body.username
    user.is_active = True
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.user_id, user.is_active)
    refresh_token = create_refresh_token(user.user_id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
