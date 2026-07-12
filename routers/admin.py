"""
routers/admin.py — Admin-only endpoints.

GET   /admin/users   → all registered users with stats
GET   /admin/stats   → platform-wide totals

Protected by AdminUser dependency — only the ADMIN_EMAIL JWT can call these.
"""
from fastapi import APIRouter
from middleware.auth import AdminUser

router = APIRouter()


@router.get("/users")
async def get_all_users(user: AdminUser):
    """Returns all registered users with their client and case counts."""
    # Phase 7: return await database.admin_get_all_profiles_with_stats()
    return {"message": "stub", "admin_email": user.email}


@router.get("/stats")
async def get_platform_stats(user: AdminUser):
    """Returns platform-wide totals: users, clients, cases, reports this month."""
    # Phase 7: return await database.admin_get_platform_stats()
    return {
        "message": "stub",
        "total_users": 0,
        "total_clients": 0,
        "total_cases": 0,
    }
