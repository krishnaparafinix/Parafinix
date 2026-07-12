"""
middleware/auth.py — Supabase JWT verification for FastAPI.

Every protected route uses get_current_user() as a FastAPI dependency.
It verifies the Supabase-issued JWT and returns the authenticated user.
Routes never trust a client-supplied user_id — always the verified one.

Usage in a router:
    from middleware.auth import CurrentUser

    @router.get("/clients")
    async def list_clients(user: CurrentUser):
        ...  # user.user_id is verified and safe to use
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from config import settings

_bearer = HTTPBearer()


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str = ""
    is_admin: bool = False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> AuthenticatedUser:
    """
    Verifies the Supabase JWT from the Authorization header.
    Returns an AuthenticatedUser on success, raises 401 on failure.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase does not set aud
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email", "")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no user ID found.",
            )
        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            is_admin=(email == settings.ADMIN_EMAIL),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


async def require_admin(user: AuthenticatedUser = Depends(get_current_user)):
    """Dependency that also checks the user is the admin account."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user


# Annotated shorthand for use in router signatures
from typing import Annotated
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
AdminUser   = Annotated[AuthenticatedUser, Depends(require_admin)]
