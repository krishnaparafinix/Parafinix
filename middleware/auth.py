"""
middleware/auth.py — Supabase JWT verification via JWKS (ES256).

Root cause of 401 errors:
  Supabase user session tokens are signed with ES256 (asymmetric).
  The JWT secret (SUPABASE_JWT_SECRET) is only used for the legacy
  anon/service_role keys. User tokens from auth.sign_in_with_password
  must be verified against Supabase's JWKS endpoint using the public key.

Token structure confirmed by Lovable integration test:
  alg:  ES256
  kid:  77d222e1-61e3-40fe-92ca-82e95b638f48
  iss:  https://oopbswfhihnvjvevesvo.supabase.co/auth/v1
  aud:  authenticated
  sub:  <user-uuid>
  email: <user-email>

Fix:
  1. Fetch JWKS from Supabase project JWKS endpoint at startup
  2. Cache the keys (refresh on key rotation)
  3. Verify token signature using the matching public key (by kid)
  4. Use PyJWT with cryptography backend for ES256 support
"""
import jwt as pyjwt
import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Annotated, Optional
from config import settings

_bearer = HTTPBearer(auto_error=False)

# ── JWKS cache ────────────────────────────────────────────────
# Fetched once at startup, refreshed on unknown kid
_jwks_cache: dict = {}  # kid -> public key

JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
SUPABASE_ISSUER = f"{settings.SUPABASE_URL}/auth/v1"


def _fetch_jwks() -> dict:
    """Fetches the JWKS from Supabase and returns a dict of kid -> key."""
    try:
        resp = httpx.get(JWKS_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        keys = {}
        for key_data in data.get("keys", []):
            kid = key_data.get("kid")
            if kid:
                # PyJWT can construct the key from the JWK dict
                public_key = pyjwt.algorithms.ECAlgorithm.from_jwk(key_data)
                keys[kid] = public_key
        return keys
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Supabase JWKS: {e}")


def _get_public_key(kid: str):
    """Returns the public key for the given kid, fetching JWKS if needed."""
    global _jwks_cache
    if kid not in _jwks_cache:
        _jwks_cache = _fetch_jwks()
    if kid not in _jwks_cache:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown signing key (kid={kid}). JWKS refresh attempted.",
        )
    return _jwks_cache[kid]


# ── User model ────────────────────────────────────────────────

class AuthenticatedUser(BaseModel):
    user_id: str
    email: str = ""
    is_admin: bool = False


# ── Token extraction ──────────────────────────────────────────

def _extract_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
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


# ── Token verification ────────────────────────────────────────

def _verify_token(token: str) -> AuthenticatedUser:
    """
    Verifies a Supabase user session JWT using ES256 + JWKS.
    Steps:
      1. Read the kid from the token header (no verification yet)
      2. Look up the corresponding EC public key from JWKS cache
      3. Verify signature, expiry, audience and issuer
      4. Extract user_id and email from payload
    """
    # Step 1: get header without verification
    try:
        header = pyjwt.get_unverified_header(token)
    except pyjwt.exceptions.DecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Malformed token: {e}",
        )

    alg = header.get("alg", "")
    kid = header.get("kid", "")

    # Step 2: get public key
    if alg == "ES256":
        public_key = _get_public_key(kid)
        decode_kwargs = {
            "algorithms": ["ES256"],
            "audience": "authenticated",
            "issuer": SUPABASE_ISSUER,
        }
    elif alg == "HS256":
        # Legacy: anon/service_role tokens — verify with JWT secret
        public_key = settings.SUPABASE_JWT_SECRET
        decode_kwargs = {
            "algorithms": ["HS256"],
            "options": {"verify_aud": False, "verify_iss": False},
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported token algorithm: {alg}",
        )

    # Step 3: verify
    try:
        payload = pyjwt.decode(token, public_key, **decode_kwargs)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except pyjwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience.",
        )
    except pyjwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer.",
        )
    except pyjwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
        )

    # Step 4: extract user
    user_id = payload.get("sub", "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID.",
        )

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


# ── FastAPI dependencies ──────────────────────────────────────

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
