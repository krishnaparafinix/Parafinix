"""
middleware/auth.py — Supabase JWT verification.

Supabase issues HS256 tokens signed with the project JWT secret.
This middleware verifies the token and extracts the authenticated user.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import BaseModel
from typing import Annotated, Optional
from config import settings

_bearer = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str = ""
    is_admin: bool = False


def _decode_supabase_token(token: str) -> dict:
    """
    Decodes a Supabase JWT. Supabase always uses HS256.
    Raises HTTPException on any failure.
    """
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    """Extracts the Bearer token from the request."""
    # From HTTPBearer dependency
    if credentials and credentials.credentials:
        return credentials.credentials
    # Direct header fallback
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Authorization: Bearer <token>",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _build_user(payload: dict) -> AuthenticatedUser:
    """Builds an AuthenticatedUser from a decoded JWT payload."""
    user_id = payload.get("sub", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID.",
        )
    # Supabase puts email at top level or inside user_metadata
    email = (
        payload.get("email")
        or payload.get("user_metadata", {}).get("email", "")
    )
    return AuthenticatedUser(
        user_id=user_id,
        email=email or "",
        is_admin=(email == settings.ADMIN_EMAIL if email else False),
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> AuthenticatedUser:
    token = _extract_token(request, credentials)
    payload = _decode_supabase_token(token)
    return _build_user(payload)


async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
AdminUser   = Annotated[AuthenticatedUser, Depends(require_admin)]
