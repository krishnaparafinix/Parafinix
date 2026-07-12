"""
app.py — Parafinix entry point.

This file is intentionally thin. It sets up the page, applies the
theme, initialises the session, and routes to the right page module.
All real logic lives in core/, auth/, documents/, and ui/.
"""
import streamlit as st
from config import APP_NAME
from ui.theme import THEME_CSS, LOGO_HEADER
from auth.auth import init_session_state, sign_out
from ui.page_login import render_login
from ui.page_clients import render_clients_page
from ui.page_cases import render_cases_page
from ui.page_generate import render_generate_page
from ui.page_factfind import render_factfind_page
from ui.page_admin import render_admin_page

st.set_page_config(page_title=f"{APP_NAME} | Your Report Wingman", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown(THEME_CSS, unsafe_allow_html=True)

init_session_state()


def main():
    if st.session_state.user is None:
        render_login()
        return

    user = st.session_state.user

    # Top bar: logo + account + log out
    top1, top2 = st.columns([4, 1.4])
    with top1:
        st.markdown(LOGO_HEADER, unsafe_allow_html=True)
    with top2:
        admin_tag = " · Admin" if user["is_admin"] else ""
        st.markdown(
            f"<div style='text-align:right;font-size:0.8rem;color:#7A8A88;padding-top:8px;'>"
            f"{user['email']}{admin_tag}</div>",
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True):
            sign_out()
            st.rerun()

    # Admin gets an extra tab
    if user["is_admin"]:
        nav = st.radio("nav", ["My Clients", "Admin Panel"], horizontal=True, label_visibility="collapsed")
        if nav == "Admin Panel":
            render_admin_page()
            return

    st.markdown("---")

    # Page routing
    page = st.session_state.page
    if page == "cases":
        render_cases_page()
    elif page == "generate":
        render_generate_page()
    elif page == "factfind":
        render_factfind_page()
    else:
        render_clients_page()


main()
