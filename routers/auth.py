"""
routers/auth.py — Authentication endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional
from middleware.auth import CurrentUser
from supabase import create_client
from config import settings

router = APIRouter()


def _db():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = ""
    firm_name: Optional[str] = ""


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(body: LoginRequest):
    """Email/password login. Returns JWT access_token + refresh_token."""
    try:
        res = _db().auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        if not res.user or not res.session:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": res.user.id,
                "email": res.user.email,
                "is_admin": res.user.email == settings.ADMIN_EMAIL,
            },
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Login failed. Check credentials.")


@router.post("/register")
async def register(body: RegisterRequest):
    """Creates a new user account."""
    try:
        db = _db()
        res = db.auth.sign_up({"email": body.email, "password": body.password})
        if not res.user:
            raise HTTPException(status_code=400, detail="Registration failed.")

        # Update profile if name/firm provided
        if body.full_name or body.firm_name:
            try:
                sess = db.auth.sign_in_with_password({
                    "email": body.email, "password": body.password
                })
                db.table("profiles").update({
                    "full_name": body.full_name,
                    "firm_name": body.firm_name,
                    "role": "admin" if body.email == settings.ADMIN_EMAIL else "user",
                }).eq("id", res.user.id).execute()
                db.auth.sign_out()
            except Exception:
                pass  # Non-fatal

        return {
            "message": "Account created. You can now log in.",
            "user": {"id": res.user.id, "email": res.user.email},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_me(user: CurrentUser, request: Request):
    """Returns the authenticated user's profile."""
    try:
        token = request.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")
        db = _db()
        db.auth.set_session(token, token)
        res = db.table("profiles").select("*").eq("id", user.user_id).execute()
        profile = res.data[0] if res.data else {}
    except Exception:
        profile = {}

    return {
        "id": user.user_id,
        "email": user.email,
        "is_admin": user.is_admin,
        "full_name": profile.get("full_name", ""),
        "firm_name": profile.get("firm_name", ""),
        "role": profile.get("role", "admin" if user.is_admin else "user"),
        "created_at": profile.get("created_at", ""),
    }


@router.post("/logout")
async def logout(user: CurrentUser, request: Request):
    """Signs out the current user."""
    try:
        token = request.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")
        db = _db()
        db.auth.set_session(token, token)
        db.auth.sign_out()
    except Exception:
        pass
    return {"message": "Logged out successfully."}


@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    """Exchanges a refresh token for a new access token."""
    try:
        res = _db().auth.refresh_session(body.refresh_token)
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token refresh failed.")


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    access_token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """
    Sends a password reset email via Supabase.
    The email contains a link that redirects to the frontend reset page
    with an access token. Frontend calls /auth/reset-password with that token.
    """
    try:
        _db().auth.reset_password_email(
            body.email,
            options={"redirect_to": f"{settings.SUPABASE_URL.replace('.supabase.co', '')}-reset-password"}
        )
    except Exception:
        pass  # Always return 200 — don't leak whether email exists
    return {"message": "If that email address is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """
    Resets the user's password using the token from the reset email.
    The frontend extracts the access_token from the URL hash and sends it here.
    """
    try:
        # Set the session with the reset token
        db = _db()
        db.auth.set_session(body.access_token, body.access_token)
        res = db.auth.update_user({"password": body.new_password})
        if not res.user:
            raise HTTPException(400, "Password reset failed.")
        return {"message": "Password updated successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Password reset failed: {e}")
