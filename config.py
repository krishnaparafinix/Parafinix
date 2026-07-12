"""
config.py — Central configuration and constants for Parafinix.
No secrets live here. Secrets come from .streamlit/secrets.toml only.
"""
import streamlit as st

APP_NAME = "Parafinix"
APP_TAGLINE = "YOUR REPORT WINGMAN"
ADMIN_EMAIL = "admin.parafinix@gmail.com"

# AI models (via Mesh API)
MODEL_DRAFTING = "anthropic/claude-opus-4.8"
MODEL_COMPLIANCE = "anthropic/claude-sonnet-4.6"

def get_secret(key: str) -> str:
    """
    Reads a secret safely and gives a clear, human-readable error
    if it's missing — instead of a raw Streamlit traceback.
    """
    try:
        return st.secrets[key]
    except Exception:
        st.error(
            f"Missing setting: **{key}**.\n\n"
            f"Add it to `.streamlit/secrets.toml` in the project folder "
            f"(the same folder as app.py), then restart the app."
        )
        st.stop()

MESH_API_KEY = get_secret("MESH_API_KEY")
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")
