from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Username must not be empty")
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )


class RegisterResponse(BaseModel):
    user_id: str
    username: str | None


class LoginRequest(BaseModel):
    username: str  # accepts username OR email — detection is in the route handler
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GooglePendingResponse(BaseModel):
    """
    Returned by GET /auth/google/callback when the Google email is not in the DB yet.

    The client must POST to /auth/google/complete with the temp_token and a chosen
    username to finish registration and receive a full JWT.
    """

    requires_username: Literal[True] = True
    temp_token: str


class CompleteGoogleRegistrationRequest(BaseModel):
    """Body for POST /auth/google/complete."""

    username: Annotated[str, StringConstraints(min_length=3, strip_whitespace=True)]
