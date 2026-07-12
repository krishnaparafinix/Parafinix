"""ui/page_login.py — Login and account creation screen."""
import streamlit as st
from ui.theme import LOGO_HEADER
from auth.auth import sign_in, sign_up

def render_login():
    st.markdown(LOGO_HEADER, unsafe_allow_html=True)
    st.markdown("<div style='max-width:440px;margin:20px auto;'>", unsafe_allow_html=True)
    st.markdown("### Welcome")
    st.caption("The AI paraplanner that turns your notes into full, compliant suitability reports.")

    tab_login, tab_signup = st.tabs(["Log in", "Create account"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log in", use_container_width=True)
            if submit:
                if not email or not password:
                    st.error("Enter email and password.")
                else:
                    ok, msg = sign_in(email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)

    with tab_signup:
        with st.form("signup_form"):
            su_name = st.text_input("Your full name")
            su_firm = st.text_input("Firm name")
            su_email = st.text_input("Email ")
            su_pass = st.text_input("Password ", type="password")
            su_pass2 = st.text_input("Confirm password", type="password")
            su_submit = st.form_submit_button("Create account", use_container_width=True)
            if su_submit:
                if not all([su_name, su_email, su_pass]):
                    st.error("Please fill in name, email and password.")
                elif su_pass != su_pass2:
                    st.error("Passwords do not match.")
                elif len(su_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    ok, msg = sign_up(su_email, su_pass, su_name, su_firm)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
    st.markdown("</div>", unsafe_allow_html=True)
