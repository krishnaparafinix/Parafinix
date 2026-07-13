"""
middleware/auth.py — Supabase JWT verification using PyJWT.

Root cause of previous 401 errors:
  python-jose incorrectly treated the Supabase JWT secret as base64url-encoded
  when the secret is a long string. This caused signature verification to fail
  even with correct credentials.

Fix:
  Switch to PyJWT which uses the secret as a raw string (correct behaviour).
  Supabase user session tokens are HS256, signed with the raw JWT secret from
  Supabase Settings > API > JWT Settings.

Token structure (from Supabase auth.sign_in_with_password):
  alg: HS256
  iss: https://<project-ref>.supabase.co/auth/v1
  sub: <user-uuid>
  email: <user-email>
  role: authenticated
  aud: authenticated
"""
import jwt as pyjwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Annotated, Optional
from config import settings

_bearer = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str = ""
    is_admin: bool = False


def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    """Extracts the Bearer token from the request."""
    if credentials and credentials.credentials:
        return credentials.credentials
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide: Authorization: Bearer <token>",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _verify_token(token: str) -> AuthenticatedUser:
    """
    Verifies a Supabase JWT using PyJWT.

    PyJWT uses the secret as a raw string — correct for Supabase.
    python-jose was incorrectly treating the secret as base64url-encoded.
    """
    try:
        payload = pyjwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={
                "verify_aud": False,   # Supabase user tokens have aud="authenticated"
                "verify_iss": False,   # Issuer varies by token type
            },
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID.",
        )

    # Email may be at top level or inside user_metadata
    email = (
        payload.get("email")
        or (payload.get("user_metadata") or {}).get("email", "")
        or ""
    )

    return AuthenticatedUser(
        user_id=user_id,
        email=email,
        is_admin=(email == settings.ADMIN_EMAIL if email else False),
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> AuthenticatedUser:
    token = _extract_token(request, credentials)
    return _verify_token(token)


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
