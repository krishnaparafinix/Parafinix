"""
routers/admin.py — Admin endpoints.

GET    /admin/users              → all users with stats
PATCH  /admin/users/{id}         → update user role  [Item 2]
GET    /admin/stats              → platform totals
GET    /admin/firm               → firm settings     [Item 3]
PUT    /admin/firm               → update firm settings [Item 3]
GET    /admin/audit              → audit log         [Item 4]
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from middleware.auth import AdminUser, CurrentUser
from supabase import create_client
from config import settings
import services.database as db
from datetime import datetime

router = APIRouter()


def _db(token: str = None):
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    if token:
        try:
            client.auth.set_session(token, token)
        except Exception:
            pass
    return client


def _token(request: Request) -> str:
    return request.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


def _log_action(user_id: str, action: str, resource_type: str = None,
                resource_id: str = None, details: dict = None, token: str = None):
    """Writes an entry to the audit_log table. Non-fatal on failure."""
    try:
        client = _db(token)
        client.table("audit_log").insert({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
        }).execute()
    except Exception:
        pass


# ── Item 2: User role management ──────────────────────────────

class UpdateRoleRequest(BaseModel):
    role: str  # "user" | "admin" | "paraplanner" | "adviser"


@router.patch("/users/{user_id}")
async def update_user_role(
    user_id: str, body: UpdateRoleRequest, admin: AdminUser, request: Request
):
    """Updates a user's role. Admin only."""
    valid_roles = {"user", "admin", "paraplanner", "adviser"}
    if body.role not in valid_roles:
        raise HTTPException(400, f"Invalid role. Must be one of: {', '.join(valid_roles)}")
    token = _token(request)
    try:
        client = _db(token)
        res = client.table("profiles").update({"role": body.role}).eq("id", user_id).execute()
        if not res.data:
            raise HTTPException(404, "User not found.")
        _log_action(admin.user_id, "UPDATE_ROLE", "user", user_id,
                    {"new_role": body.role}, token)
        return {"message": "Role updated.", "user_id": user_id, "role": body.role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Could not update role: {e}")


# ── Items GET /admin/users and /admin/stats ───────────────────

@router.get("/users")
async def get_all_users(admin: AdminUser):
    profiles = db.admin_get_all_profiles()
    all_clients = db.admin_get_all_clients()
    all_cases = db.admin_get_all_cases()
    rows = []
    for p in profiles:
        uid = p.get("id")
        rows.append({
            "id": uid,
            "name": p.get("full_name", ""),
            "email": p.get("email", ""),
            "firm": p.get("firm_name", ""),
            "role": p.get("role", "user"),
            "clients": sum(1 for c in all_clients if c.get("user_id") == uid),
            "cases": sum(1 for c in all_cases if c.get("user_id") == uid),
            "pending": sum(1 for c in all_cases if c.get("user_id") == uid
                          and c.get("status") in ("draft", "in_review")),
            "joined": (p.get("created_at") or "")[:10],
        })
    return {"users": rows, "total": len(rows)}


@router.get("/stats")
async def get_platform_stats(admin: AdminUser):
    profiles = db.admin_get_all_profiles()
    all_clients = db.admin_get_all_clients()
    all_cases = db.admin_get_all_cases()
    month = datetime.now().strftime("%Y-%m")
    return {
        "total_users": len(profiles),
        "total_clients": len(all_clients),
        "total_cases": len(all_cases),
        "cases_this_month": sum(1 for c in all_cases
                                if (c.get("created_at") or "").startswith(month)),
        "pending_review": sum(1 for c in all_cases
                              if c.get("status") in ("draft", "in_review")),
    }


# ── Item 3: Firm settings ─────────────────────────────────────

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


@router.get("/firm")
async def get_firm_settings(user: CurrentUser, request: Request):
    """Returns the firm settings for the authenticated user."""
    token = _token(request)
    try:
        client = _db(token)
        res = client.table("firm_settings").select("*").eq("user_id", user.user_id).execute()
        if res.data:
            return res.data[0]
        # Return empty defaults if not set yet
        return {
            "user_id": user.user_id,
            "firm_name": "", "fca_number": "", "address": "",
            "phone": "", "email": "", "website": "",
            "basis_of_advice": "Independent", "adviser_charges": "", "logo_url": "",
        }
    except Exception as e:
        raise HTTPException(500, f"Could not load firm settings: {e}")


@router.put("/firm")
@router.patch("/firm")
async def update_firm_settings(
    body: FirmSettingsRequest, user: CurrentUser, request: Request
):
    """Creates or updates firm settings for the authenticated user."""
    token = _token(request)
    try:
        client = _db(token)
        data = {k: v for k, v in body.dict().items() if v is not None}
        data["user_id"] = user.user_id
        data["updated_at"] = datetime.utcnow().isoformat()

        # Upsert based on user_id
        res = client.table("firm_settings").upsert(
            data, on_conflict="user_id"
        ).execute()
        _log_action(user.user_id, "UPDATE_FIRM_SETTINGS", "firm_settings",
                    user.user_id, data, token)
        return res.data[0] if res.data else data
    except Exception as e:
        raise HTTPException(500, f"Could not update firm settings: {e}")


# ── Item 4: Audit log ─────────────────────────────────────────

@router.get("/audit")
async def get_audit_log(
    user: CurrentUser, request: Request,
    limit: int = 100, offset: int = 0
):
    """
    Returns audit log entries.
    Admins see all entries. Regular users see only their own.
    """
    token = _token(request)
    try:
        client = _db(token)
        query = client.table("audit_log").select("*").order("created_at", desc=True)

        if not user.is_admin:
            query = query.eq("user_id", user.user_id)

        query = query.range(offset, offset + limit - 1)
        res = query.execute()
        entries = res.data or []
        return {
            "entries": entries,
            "total": len(entries),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(500, f"Could not load audit log: {e}")
