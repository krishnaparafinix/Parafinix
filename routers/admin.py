"""
routers/admin.py — Admin endpoints.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, require_admin, AuthenticatedUser
from supabase import create_client
from config import settings
import services.database as db
from datetime import datetime

router = APIRouter()


def _db(token: str = None):
    c = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    if token:
        try: c.auth.set_session(token, token)
        except Exception: pass
    return c


def _token(r: Request) -> str:
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


def _log(user_id, action, resource_type=None, resource_id=None, details=None, token=None):
    try:
        _db(token).table("audit_log").insert({
            "user_id": user_id, "action": action,
            "resource_type": resource_type, "resource_id": resource_id,
            "details": details or {},
        }).execute()
    except Exception:
        pass


class UpdateRoleRequest(BaseModel):
    role: str


class FirmSettingsRequest(BaseModel):
    firm_name: Optional[str] = None
    fca_number: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    basis_of_advice: Optional[str] = None
    adviser_charges: Optional[str] = None
    logo_url: Optional[str] = None


@router.get("/users")
async def get_all_users(admin: AuthenticatedUser = Depends(require_admin)):
    profiles = db.admin_get_all_profiles()
    all_clients = db.admin_get_all_clients()
    all_cases = db.admin_get_all_cases()
    return {"users": [{
        "id": p.get("id"), "name": p.get("full_name", ""),
        "email": p.get("email", ""), "firm": p.get("firm_name", ""),
        "role": p.get("role", "user"),
        "clients": sum(1 for c in all_clients if c.get("user_id") == p.get("id")),
        "cases": sum(1 for c in all_cases if c.get("user_id") == p.get("id")),
        "pending": sum(1 for c in all_cases if c.get("user_id") == p.get("id")
                      and c.get("status") in ("draft","in_review")),
        "joined": (p.get("created_at") or "")[:10],
    } for p in profiles], "total": len(profiles)}


@router.patch("/users/{user_id}")
async def update_user_role(
    user_id: str,
    request: Request,
    body: UpdateRoleRequest,
    admin: AuthenticatedUser = Depends(require_admin),
):
    valid = {"user", "admin", "paraplanner", "adviser"}
    if body.role not in valid:
        raise HTTPException(400, f"Role must be one of: {', '.join(valid)}")
    token = _token(request)
    try:
        res = _db(token).table("profiles").update({"role": body.role}).eq("id", user_id).execute()
        if not res.data:
            raise HTTPException(404, "User not found.")
        _log(admin.user_id, "UPDATE_ROLE", "user", user_id, {"new_role": body.role}, token)
        return {"message": "Role updated.", "user_id": user_id, "role": body.role}
    except HTTPException: raise
    except Exception as e: raise HTTPException(500, f"Could not update role: {e}")


@router.get("/stats")
async def get_platform_stats(admin: AuthenticatedUser = Depends(require_admin)):
    profiles = db.admin_get_all_profiles()
    all_clients = db.admin_get_all_clients()
    all_cases = db.admin_get_all_cases()
    month = datetime.now().strftime("%Y-%m")
    return {
        "total_users": len(profiles),
        "total_clients": len(all_clients),
        "total_cases": len(all_cases),
        "cases_this_month": sum(1 for c in all_cases if (c.get("created_at") or "").startswith(month)),
        "pending_review": sum(1 for c in all_cases if c.get("status") in ("draft","in_review")),
    }


@router.get("/firm")
async def get_firm_settings(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    try:
        res = _db(token).table("firm_settings").select("*").eq("user_id", user.user_id).execute()
        if res.data:
            return res.data[0]
        return {"user_id": user.user_id, "firm_name": "", "fca_number": "",
                "address": "", "phone": "", "email": "", "website": "",
                "basis_of_advice": "Independent", "adviser_charges": "", "logo_url": ""}
    except Exception as e:
        raise HTTPException(500, f"Could not load firm settings: {e}")


@router.put("/firm")
@router.patch("/firm")
async def update_firm_settings(
    request: Request,
    body: FirmSettingsRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    try:
        data = {k: v for k, v in body.dict().items() if v is not None}
        data["user_id"] = user.user_id
        data["updated_at"] = datetime.utcnow().isoformat()
        res = _db(token).table("firm_settings").upsert(data, on_conflict="user_id").execute()
        _log(user.user_id, "UPDATE_FIRM_SETTINGS", "firm_settings", user.user_id, data, token)
        return res.data[0] if res.data else data
    except Exception as e:
        raise HTTPException(500, f"Could not update firm settings: {e}")


@router.get("/audit")
async def get_audit_log(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0,
):
    token = _token(request)
    try:
        client = _db(token)
        query = client.table("audit_log").select("*").order("created_at", desc=True)
        if not user.is_admin:
            query = query.eq("user_id", user.user_id)
        res = query.range(offset, offset + limit - 1).execute()
        entries = res.data or []
        return {"entries": entries, "total": len(entries), "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(500, f"Could not load audit log: {e}")
