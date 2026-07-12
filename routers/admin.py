"""
routers/admin.py — Admin-only endpoints.

GET   /admin/users   → all registered users with stats
GET   /admin/stats   → platform-wide totals

Protected by AdminUser — only the ADMIN_EMAIL JWT can call these.
"""
from fastapi import APIRouter
from middleware.auth import AdminUser
import services.database as db

router = APIRouter()


@router.get("/users")
async def get_all_users(user: AdminUser):
    """Returns all registered users with their client and case counts."""
    profiles = db.admin_get_all_profiles()
    all_clients = db.admin_get_all_clients()
    all_cases = db.admin_get_all_cases()

    rows = []
    for p in profiles:
        uid = p.get("id")
        rows.append({
            "id": uid,
            "name": p.get("full_name") or "",
            "email": p.get("email") or "",
            "firm": p.get("firm_name") or "",
            "role": p.get("role") or "user",
            "clients": sum(1 for c in all_clients if c.get("user_id") == uid),
            "cases": sum(1 for c in all_cases if c.get("user_id") == uid),
            "pending": sum(1 for c in all_cases
                          if c.get("user_id") == uid
                          and c.get("status") in ("draft", "in_review")),
            "joined": (p.get("created_at") or "")[:10],
        })
    return {"users": rows, "total": len(rows)}


@router.get("/stats")
async def get_platform_stats(user: AdminUser):
    """Returns platform-wide totals."""
    profiles = db.admin_get_all_profiles()
    all_clients = db.admin_get_all_clients()
    all_cases = db.admin_get_all_cases()

    from datetime import datetime
    month = datetime.now().strftime("%Y-%m")
    this_month = sum(1 for c in all_cases
                     if (c.get("created_at") or "").startswith(month))
    pending = sum(1 for c in all_cases
                  if c.get("status") in ("draft", "in_review"))

    return {
        "total_users": len(profiles),
        "total_clients": len(all_clients),
        "total_cases": len(all_cases),
        "cases_this_month": this_month,
        "pending_review": pending,
    }
