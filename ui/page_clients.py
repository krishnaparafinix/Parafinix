"""
ui/page_clients.py — Dashboard + client folder list.

On login the user sees:
  - Four stat cards (clients, total reports, this month, pending review)
  - A quick-add client form
  - Their client folders as cards, each showing last activity and report count
"""
import streamlit as st
from core.database import get_clients, create_client_folder, delete_client_folder, get_cases, get_user_stats


def render_clients_page():
    user = st.session_state.user

    # ── Dashboard stats ──
    st.markdown("### Dashboard")
    stats = get_user_stats(user["id"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clients", stats["clients"])
    m2.metric("Reports total", stats["reports"])
    m3.metric("This month", stats["this_month"])
    m4.metric("Pending review", stats["pending_review"])

    st.markdown("---")

    # ── Add new client ──
    st.markdown("### Your Clients")
    clients_check = get_clients(user["id"])
    with st.expander("Add a new client", expanded=len(clients_check) == 0):
        with st.form("new_client_form"):
            new_name = st.text_input("Client name", placeholder="e.g. Mr & Mrs David Thompson")
            submitted = st.form_submit_button("Create client folder", use_container_width=True)
            if submitted:
                if new_name.strip():
                    result = create_client_folder(user["id"], new_name.strip())
                    if result:
                        st.success(f"Created folder for {new_name.strip()}")
                        st.rerun()
                else:
                    st.error("Please enter a client name.")

    # ── Client folder list ──
    clients = get_clients(user["id"])
    if not clients:
        st.info("No clients yet. Use the form above to create your first client folder.")
        return

    for c in clients:
        cases = get_cases(c["id"])
        n_reports = len(cases)
        last_updated = c.get("updated_at", "")[:10] if c.get("updated_at") else "—"

        # Status summary for the most recent report
        latest_status = ""
        if cases:
            s = cases[0].get("status", "draft")
            latest_status = {"draft": "Draft", "in_review": "In Review", "signed_off": "Signed Off"}.get(s, s)

        col1, col2, col3 = st.columns([5, 1.5, 1])
        with col1:
            rag = cases[0].get("rag_rating", "") if cases else ""
            rag_dot = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}.get(rag, "⚪")
            report_word = "report" if n_reports == 1 else "reports"
            status_bit = f"&nbsp;·&nbsp; {rag_dot} {latest_status}" if latest_status else ""
            st.markdown(
                f'''<div class="folder-card">
                <div class="folder-name">{c["client_name"]}</div>
                <div class="folder-meta">
                    {n_reports} {report_word} &nbsp;·&nbsp; Last activity: {last_updated}{status_bit}
                </div></div>''',
                unsafe_allow_html=True
            )
        with col2:
            if st.button("Open", key=f"open_{c['id']}", use_container_width=True):
                st.session_state.active_client_id = c["id"]
                st.session_state.active_client_name = c["client_name"]
                st.session_state.page = "cases"
                st.rerun()
        with col3:
            if st.button("Del", key=f"del_{c['id']}", use_container_width=True):
                delete_client_folder(c["id"])
                st.rerun()
