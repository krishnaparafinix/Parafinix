"""
ui/page_admin.py — Admin panel.
Shows every user, their firm, client count, report count, and join date.
"""
import streamlit as st
import pandas as pd
from core.database import admin_get_all_profiles, admin_get_all_clients, admin_get_all_cases


def render_admin_page():
    st.markdown("### Admin Panel")
    st.caption("Full platform view — all users, clients, and reports.")

    profiles = admin_get_all_profiles()
    all_clients = admin_get_all_clients()
    all_cases = admin_get_all_cases()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total users", len(profiles))
    m2.metric("Total client folders", len(all_clients))
    m3.metric("Total reports", len(all_cases))

    st.markdown("---")
    st.markdown("#### All users")
    if not profiles:
        st.info("No users registered yet.")
        return

    rows = []
    for p in profiles:
        uid = p.get("id")
        uc = sum(1 for c in all_clients if c.get("user_id") == uid)
        ur = sum(1 for c in all_cases if c.get("user_id") == uid)
        pending = sum(1 for c in all_cases
                      if c.get("user_id") == uid and c.get("status") in ("draft", "in_review"))
        rows.append({
            "Name": p.get("full_name") or "—",
            "Email": p.get("email") or "—",
            "Firm": p.get("firm_name") or "—",
            "Role": p.get("role") or "user",
            "Clients": uc,
            "Reports": ur,
            "Pending": pending,
            "Joined": (p.get("created_at") or "")[:10],
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### Recent reports (all users)")
    if all_cases:
        case_rows = []
        client_map = {c["id"]: c.get("client_name","—") for c in all_clients}
        for case in sorted(all_cases, key=lambda x: x.get("created_at",""), reverse=True)[:20]:
            case_rows.append({
                "Report": case.get("case_title","—"),
                "Client": client_map.get(case.get("client_id",""),"—"),
                "RAG": case.get("rag_rating","—"),
                "Status": case.get("status","—"),
                "Saved": (case.get("created_at",""))[:10],
            })
        st.dataframe(pd.DataFrame(case_rows), use_container_width=True, hide_index=True)
