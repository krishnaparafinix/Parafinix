"""
core/database.py — Every Supabase call lives here, nowhere else.
This is the ONLY file that talks to the database directly.
UI code calls these functions; it never touches Supabase itself.
"""
from supabase import create_client, Client
import streamlit as st
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_ANON_KEY

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def _restore_session():
    """
    Re-attaches the logged-in user's session token before every
    database call. Without this, Row Level Security rejects the
    request because the database can't confirm who's asking.
    """
    user = st.session_state.get("user")
    if user and user.get("access_token"):
        try:
            get_supabase().auth.set_session(user["access_token"], user["refresh_token"])
        except Exception:
            pass

# ── CLIENTS ──────────────────────────────────────
def get_clients(user_id: str) -> list:
    _restore_session()
    try:
        res = get_supabase().table("clients").select("*") \
            .eq("user_id", user_id).order("updated_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Could not load clients: {e}")
        return []

def create_client_folder(user_id: str, client_name: str):
    _restore_session()
    try:
        res = get_supabase().table("clients").insert({
            "user_id": user_id, "client_name": client_name
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Could not create client folder: {e}")
        return None

def delete_client_folder(client_id: str) -> bool:
    _restore_session()
    try:
        get_supabase().table("clients").delete().eq("id", client_id).execute()
        return True
    except Exception as e:
        st.error(f"Could not delete client: {e}")
        return False

def get_client_by_id(client_id: str) -> dict:
    _restore_session()
    try:
        res = get_supabase().table("clients").select("*").eq("id", client_id).single().execute()
        return res.data or {}
    except Exception:
        return {}

def update_client_fact_find(client_id: str, data: dict, notes: str) -> bool:
    """Persists extracted/edited fact-find data permanently on the client record."""
    _restore_session()
    try:
        get_supabase().table("clients").update({
            "fact_find_data": data, "fact_find_notes": notes
        }).eq("id", client_id).execute()
        return True
    except Exception as e:
        st.error(f"Could not save client details: {e}")
        return False

# ── CASES (generated reports) ──────────────────────────────────────
def get_cases(client_id: str) -> list:
    _restore_session()
    try:
        res = get_supabase().table("cases").select("*") \
            .eq("client_id", client_id).order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Could not load reports: {e}")
        return []

def save_case(user_id: str, client_id: str, case_title: str, fact_find: str,
              part1: str, part2: str, compliance: str,
              part3: str = "", part4: str = "",
              rag_rating: str = "", passes: int = 0, flags: int = 0, fails: int = 0,
              firm_name: str = "", adviser_name: str = "", basis: str = "",
              charges: str = "", report_ref: str = "", status: str = "draft",
              version: int = 1):
    """Saves a generated report (3-pass). All text needed to regenerate
    the Word documents on demand is stored — no binary files kept."""
    _restore_session()
    try:
        res = get_supabase().table("cases").insert({
            "user_id": user_id, "client_id": client_id, "case_title": case_title,
            "fact_find": fact_find, "report_part1": part1, "report_part2": part2,
            "report_part3": part3, "report_part4": part4,
            "compliance_result": compliance, "rag_rating": rag_rating,
            "passes": passes, "flags": flags, "fails": fails,
            "firm_name": firm_name, "adviser_name": adviser_name, "basis": basis,
            "charges": charges, "report_ref": report_ref,
            "status": status, "version": version,
        }).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Could not save report: {e}")
        return None

def update_case_status(case_id: str, new_status: str) -> bool:
    """Move a report through the workflow: draft -> in_review -> signed_off."""
    _restore_session()
    try:
        get_supabase().table("cases").update({"status": new_status}).eq("id", case_id).execute()
        return True
    except Exception as e:
        st.error(f"Could not update status: {e}")
        return False

def get_next_version(client_id: str) -> int:
    """Returns the next version number for this client's reports."""
    _restore_session()
    try:
        res = get_supabase().table("cases").select("version") \
            .eq("client_id", client_id).order("version", desc=True).limit(1).execute()
        if res.data:
            return (res.data[0].get("version") or 0) + 1
        return 1
    except Exception:
        return 1

def delete_case(case_id: str) -> bool:
    _restore_session()
    try:
        get_supabase().table("cases").delete().eq("id", case_id).execute()
        return True
    except Exception as e:
        st.error(f"Could not delete report: {e}")
        return False

# ── DASHBOARD STATS ──────────────────────────────────────
def get_user_stats(user_id: str) -> dict:
    """Counts for the dashboard: clients, total reports, reports this
    month, and reports pending review."""
    _restore_session()
    stats = {"clients": 0, "reports": 0, "this_month": 0, "pending_review": 0}
    try:
        clients = get_supabase().table("clients").select("id").eq("user_id", user_id).execute()
        stats["clients"] = len(clients.data or [])
        cases = get_supabase().table("cases").select("created_at,status").eq("user_id", user_id).execute()
        data = cases.data or []
        stats["reports"] = len(data)
        month_prefix = datetime.now().strftime("%Y-%m")
        stats["this_month"] = sum(1 for c in data if (c.get("created_at") or "").startswith(month_prefix))
        stats["pending_review"] = sum(1 for c in data if c.get("status") in ("draft", "in_review"))
    except Exception:
        pass
    return stats

# ── ADMIN ──────────────────────────────────────────
def admin_get_all_profiles() -> list:
    _restore_session()
    try:
        res = get_supabase().table("profiles").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def admin_get_all_clients() -> list:
    _restore_session()
    try:
        res = get_supabase().table("clients").select("*").execute()
        return res.data or []
    except Exception:
        return []

def admin_get_all_cases() -> list:
    _restore_session()
    try:
        res = get_supabase().table("cases").select("*").execute()
        return res.data or []
    except Exception:
        return []
