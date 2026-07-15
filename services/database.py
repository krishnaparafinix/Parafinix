"""
services/database.py — All Supabase operations for the FastAPI backend.

Extracted from core/database.py in the Streamlit app.
Changes from Streamlit version:
  - Removed @st.cache_resource and st.session_state dependencies
  - Removed _restore_session() — the FastAPI middleware passes the JWT
    directly so each call uses the authenticated client explicitly
  - Replaced st.error() with HTTPException
  - get_supabase_client() takes the user's JWT token and creates an
    authenticated client for that request — RLS works identically

Logic and SQL operations are identical to the Streamlit reference.
"""
from fastapi import HTTPException, status
from datetime import datetime
from config import settings


def get_supabase_client(access_token: str | None = None):
    """
    Returns a Supabase client.
    Uses shared anon client for admin ops, user client for RLS-protected ops.
    """
    if access_token:
        return get_user_client(access_token)
    return get_anon_client()


# ── CLIENTS ──────────────────────────────────────────────────

def get_clients(user_id: str, access_token: str) -> list:
    db = get_supabase_client(access_token)
    try:
        res = db.table("clients").select("*") \
            .eq("user_id", user_id).order("updated_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load clients: {e}")


def create_client_folder(user_id: str, client_name: str, access_token: str):
    db = get_supabase_client(access_token)
    try:
        res = db.table("clients").insert({
            "user_id": user_id, "client_name": client_name
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create client: {e}")


def delete_client_folder(client_id: str, access_token: str) -> bool:
    db = get_supabase_client(access_token)
    try:
        db.table("clients").delete().eq("id", client_id).execute()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not delete client: {e}")


# ── CASES ────────────────────────────────────────────────────

def get_cases(client_id: str, access_token: str) -> list:
    db = get_supabase_client(access_token)
    try:
        res = db.table("cases").select("*") \
            .eq("client_id", client_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load cases: {e}")


def get_case(case_id: str, access_token: str):
    db = get_supabase_client(access_token)
    try:
        res = db.table("cases").select("*").eq("id", case_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Case not found.")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load case: {e}")


def save_case(user_id: str, client_id: str, case_title: str, fact_find: str,
              part1: str, part2: str, compliance: str,
              part3: str = "", part4: str = "",
              rag_rating: str = "", passes: int = 0, flags: int = 0, fails: int = 0,
              firm_name: str = "", adviser_name: str = "", basis: str = "",
              charges: str = "", report_ref: str = "", status: str = "draft",
              version: int = 1, access_token: str = ""):
    db = get_supabase_client(access_token)
    try:
        res = db.table("cases").insert({
            "user_id": user_id, "client_id": client_id, "case_title": case_title,
            "fact_find": fact_find,
            "report_part1": part1, "report_part2": part2,
            "report_part3": part3, "report_part4": part4,
            "compliance_result": compliance, "rag_rating": rag_rating,
            "passes": passes, "flags": flags, "fails": fails,
            "firm_name": firm_name, "adviser_name": adviser_name,
            "basis": basis, "charges": charges, "report_ref": report_ref,
            "status": status, "version": version,
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save case: {e}")


def update_case_status(case_id: str, new_status: str, access_token: str) -> bool:
    db = get_supabase_client(access_token)
    try:
        db.table("cases").update({"status": new_status}).eq("id", case_id).execute()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not update status: {e}")


def delete_case(case_id: str, access_token: str) -> bool:
    db = get_supabase_client(access_token)
    try:
        db.table("cases").delete().eq("id", case_id).execute()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not delete case: {e}")


def get_next_version(client_id: str, access_token: str) -> int:
    db = get_supabase_client(access_token)
    try:
        res = db.table("cases").select("version") \
            .eq("client_id", client_id).order("version", desc=True).limit(1).execute()
        if res.data:
            return (res.data[0].get("version") or 0) + 1
        return 1
    except Exception:
        return 1


# ── DASHBOARD STATS ──────────────────────────────────────────

def get_user_stats(user_id: str, access_token: str) -> dict:
    db = get_supabase_client(access_token)
    stats = {"clients": 0, "reports": 0, "this_month": 0, "pending_review": 0}
    try:
        clients = db.table("clients").select("id").eq("user_id", user_id).execute()
        stats["clients"] = len(clients.data or [])
        cases = db.table("cases").select("created_at,status").eq("user_id", user_id).execute()
        data = cases.data or []
        stats["reports"] = len(data)
        month_prefix = datetime.now().strftime("%Y-%m")
        stats["this_month"] = sum(1 for c in data if (c.get("created_at") or "").startswith(month_prefix))
        stats["pending_review"] = sum(1 for c in data if c.get("status") in ("draft", "in_review"))
    except Exception:
        pass
    return stats


# ── ADMIN ────────────────────────────────────────────────────

def admin_get_all_profiles() -> list:
    db = get_supabase_client(None)
    try:
        res = db.table("profiles").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []


def admin_get_all_clients() -> list:
    db = get_supabase_client(None)
    try:
        res = db.table("clients").select("*").execute()
        return res.data or []
    except Exception:
        return []


def admin_get_all_cases() -> list:
    db = get_supabase_client(None)
    try:
        res = db.table("cases").select("*").execute()
        return res.data or []
    except Exception:
        return []
