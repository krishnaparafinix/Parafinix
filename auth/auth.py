"""
auth/auth.py — Sign up, sign in, sign out, and session state.
The rest of the app never talks to Supabase Auth directly — it
calls these functions and reads st.session_state.user.
"""
import streamlit as st
from core.database import get_supabase
from config import ADMIN_EMAIL

def init_session_state():
    defaults = {
        "user": None,
        "active_client_id": None,
        "active_client_name": None,
        "loaded_case": None,
        "page": "clients",
        "_show_ff_outputs": False,
        "_ff_confirmed_data": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def sign_up(email: str, password: str, full_name: str, firm_name: str):
    try:
        res = get_supabase().auth.sign_up({"email": email, "password": password})
        if res.user:
            try:
                # Sign in briefly to get a valid session to update the profile row
                get_supabase().auth.sign_in_with_password({"email": email, "password": password})
                get_supabase().table("profiles").update({
                    "full_name": full_name,
                    "firm_name": firm_name,
                    "role": "admin" if email == ADMIN_EMAIL else "user",
                }).eq("id", res.user.id).execute()
                get_supabase().auth.sign_out()
            except Exception:
                pass
            return True, "Account created. You can now log in."
        return False, "Sign up failed. Please try again."
    except Exception as e:
        return False, str(e)

def sign_in(email: str, password: str):
    try:
        res = get_supabase().auth.sign_in_with_password({"email": email, "password": password})
        if res.user and res.session:
            st.session_state.user = {
                "id": res.user.id,
                "email": res.user.email,
                "is_admin": res.user.email == ADMIN_EMAIL,
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
            }
            return True, "Logged in."
        return False, "Login failed. Check your email and password."
    except Exception as e:
        return False, str(e)

def sign_out():
    try:
        get_supabase().auth.sign_out()
    except Exception:
        pass
    for key in ["user", "active_client_id", "active_client_name", "loaded_case"]:
        st.session_state[key] = None
    st.session_state.page = "clients"

def current_user():
    return st.session_state.get("user")

def is_logged_in() -> bool:
    return st.session_state.get("user") is not None
