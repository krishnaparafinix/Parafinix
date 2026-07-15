"""
services/supabase_client.py — Shared Supabase client pool.

Creates ONE Supabase client at module import time (equivalent to
Streamlit's @st.cache_resource). This eliminates the per-request
connection overhead that was causing login timeouts.

For authenticated requests, we create a thin session-scoped client
that reuses the same connection settings but sets the user JWT.
"""
from supabase import create_client, Client
from config import settings

# ── Shared anon client — created once at startup ──────────────
_anon_client: Client = None


def get_anon_client() -> Client:
    """Returns the shared anon Supabase client. Created once, reused forever."""
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _anon_client


def get_user_client(access_token: str) -> Client:
    """
    Returns a Supabase client with the user's JWT session set.
    Creates a new client per request (required for RLS isolation)
    but reuses the same URL/key so the HTTP connection is fast.
    """
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    if access_token:
        try:
            client.auth.set_session(access_token, access_token)
        except Exception:
            pass
    return client


def warmup():
    """
    Called at startup to establish the initial connection.
    Prevents the first real request from bearing the full cold-start cost.
    """
    try:
        client = get_anon_client()
        # Lightweight ping - just check the client initialised
        _ = client.table("profiles").select("id").limit(1).execute()
        print("Supabase connection warmed up ✅")
    except Exception as e:
        print(f"Supabase warmup skipped ({e}) — will connect on first request")
