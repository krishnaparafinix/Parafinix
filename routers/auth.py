"""
routers/auth.py — Authentication endpoints for the Lovable React frontend.

The Lovable frontend calls Supabase directly for login/signup via the
Supabase JS SDK. These endpoints provide:
  - POST /auth/login    → validates credentials via Supabase, returns JWT
  - GET  /auth/me       → returns current user profile from verified JWT
  - POST /auth/logout   → invalidates the Supabase session server-side
  - POST /auth/register → creates a new user account

All existing endpoints already accept Authorization: Bearer <token>
via the get_current_user dependency in middleware/auth.py.
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from middleware.auth import CurrentUser
from supabase import create_client
from config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""
    firm_name: Optional[str] = ""


@router.post("/login")
async def login(body: LoginRequest):
    """
    Authenticates a user with email and password via Supabase.
    Returns the access token (JWT) and user details.
    The Lovable frontend stores the token and sends it as
    Authorization: Bearer <token> on every subsequent request.
    """
    try:
        db = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        res = db.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        if not res.user or not res.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "is_admin": res.user.email == settings.ADMIN_EMAIL,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed. Please check your email and password.",
        )


@router.post("/register")
async def register(body: RegisterRequest):
    """
    Creates a new user account via Supabase.
    Also updates the profile row with full name and firm name.
    """
    try:
        db = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        res = db.auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
        if not res.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed.",
            )
        # Update profile with name and firm
        if body.full_name or body.firm_name:
            try:
                # Sign in to get a session for the profile update
                sess = db.auth.sign_in_with_password({
                    "email": body.email,
                    "password": body.password,
                })
                db.table("profiles").update({
                    "full_name": body.full_name,
                    "firm_name": body.firm_name,
                    "role": "admin" if body.email == settings.ADMIN_EMAIL else "user",
                }).eq("id", res.user.id).execute()
                db.auth.sign_out()
            except Exception:
                pass  # Profile update failure is non-fatal

        return {
            "message": "Account created successfully. You can now log in.",
            "user": {
                "id": res.user.id,
                "email": res.user.email,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me")
async def get_me(user: CurrentUser, request: Request):
    """
    Returns the current user's profile from the verified JWT.
    Also fetches full name and firm name from the profiles table.
    """
    try:
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        db = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        db.auth.set_session(token, token)
        res = db.table("profiles").select("*").eq("id", user.user_id).execute()
        profile = res.data[0] if res.data else {}
        return {
            "id": user.user_id,
            "email": user.email,
            "is_admin": user.is_admin,
            "full_name": profile.get("full_name", ""),
            "firm_name": profile.get("firm_name", ""),
            "role": profile.get("role", "user"),
            "created_at": profile.get("created_at", ""),
        }
    except Exception as e:
        # Return basic info from JWT even if profile fetch fails
        return {
            "id": user.user_id,
            "email": user.email,
            "is_admin": user.is_admin,
            "full_name": "",
            "firm_name": "",
            "role": "admin" if user.is_admin else "user",
        }


@router.post("/logout")
async def logout(user: CurrentUser, request: Request):
    """
    Signs out the current user server-side via Supabase.
    The Lovable frontend should also clear its local token storage.
    """
    try:
        token = request.headers.get("authorization", "").replace("Bearer ", "")
        db = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        db.auth.set_session(token, token)
        db.auth.sign_out()
    except Exception:
        pass  # Sign out failure is non-fatal — token will expire naturally
    return {"message": "Logged out successfully."}


@router.post("/refresh")
async def refresh_token(body: dict):
    """
    Refreshes an expired access token using a refresh token.
    The Lovable frontend calls this when it receives a 401.
    """
    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required.")
    try:
        db = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        res = db.auth.refresh_session(refresh_token)
        if not res.session:
            raise HTTPException(status_code=401, detail="Refresh token is invalid or expired.")
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token refresh failed.")
