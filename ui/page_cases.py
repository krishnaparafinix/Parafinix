"""
ui/page_cases.py — Client profile: details, document generation, and report history.
"""
import streamlit as st
from datetime import datetime
from core.database import get_cases, delete_case, update_case_status, get_client_by_id
from documents.regenerate import suitability_from_case, compliance_from_case
from documents.factfind_doc import build_factfind_doc

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

STATUS_LABELS = {
    "draft":     ("Draft",      "🔵", "flag"),
    "in_review": ("In Review",  "🟡", "flag"),
    "signed_off":("Signed Off", "🟢", "pass"),
}
STATUS_FLOW = {
    "draft":     "in_review",
    "in_review": "signed_off",
    "signed_off": None,
}
STATUS_NEXT_LABEL = {
    "draft":     "Send for Review →",
    "in_review": "Mark Signed Off ✓",
    "signed_off": None,
}
RAG_CLASS = {"GREEN": "pass", "AMBER": "flag", "RED": "miss"}


def _format_date(iso_str: str) -> str:
    try:
        return datetime.fromisoformat(iso_str.replace("Z","")).strftime("%d %b %Y, %H:%M")
    except Exception:
        return iso_str[:10] if iso_str else "—"


def render_cases_page():
    user = st.session_state.user
    cid = st.session_state.active_client_id
    cname = st.session_state.active_client_name

    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(f"### {cname}")
        st.caption("Client profile — details, documents, and report history all in one place.")
    with col_b:
        if st.button("← Back to clients", use_container_width=True):
            st.session_state.page = "clients"
            st.session_state.active_client_id = None
            st.session_state.active_client_name = None
            st.rerun()

    st.markdown("---")

    # ── CLIENT DETAILS ──────────────────────────────────
    client_record = get_client_by_id(cid)
    ff_data = client_record.get("fact_find_data")

    st.markdown("#### Client details")

    if ff_data:
        p = ff_data.get("personal", {})
        obj = ff_data.get("objectives", {})
        flags = [f for f in ff_data.get("flags", []) if f and f.strip()]
        summary_bits = []
        if p.get("client1_name"): summary_bits.append(p["client1_name"])
        if p.get("client2_name"): summary_bits.append(p["client2_name"])
        names = " & ".join(summary_bits) or cname
        st.markdown(f"""
        <div class="pfx-card">
            <div style="font-weight:700;color:#0B1F3A;font-size:1.05rem;margin-bottom:6px;">{names}</div>
            <div style="font-size:0.85rem;color:#64748B;margin-bottom:4px;">
                {p.get('client1_employment','') or 'Employment not recorded'}
            </div>
            <div style="font-size:0.85rem;color:#64748B;">
                Primary objective: {obj.get('primary_objective','') or 'Not recorded'}
            </div>
            {f'<div style="margin-top:8px;color:#B8860B;font-size:0.82rem;">⚠ {len(flags)} item(s) flagged for review</div>' if flags else ''}
        </div>
        """, unsafe_allow_html=True)
        if st.button("View / edit full details →", use_container_width=True):
            st.session_state.page = "factfind"
            st.rerun()
    else:
        st.markdown("""
        <div class="pfx-card">
            <div style="font-weight:700;color:#0B1F3A;margin-bottom:4px;">No details on file yet</div>
            <div style="font-size:0.85rem;color:#64748B;">Type details directly, upload a document for AI to extract, or paste meeting notes.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Add client details →", type="primary", use_container_width=True):
            st.session_state.page = "factfind"
            st.rerun()

    st.markdown("---")

    # ── GENERATE ──────────────────────────────────
    st.markdown("#### Generate documents")
    gen_col1, gen_col2 = st.columns(2)
    with gen_col1:
        st.markdown("""
        <div class="pfx-card" style="min-height:90px;border-left:4px solid #F5B841;">
            <div style="font-weight:700;color:#0B1F3A;margin-bottom:4px;">Fact-Find Document</div>
            <div style="font-size:0.82rem;color:#64748B;">
                Generates from saved details, or a blank template if none exist yet.
            </div>
        </div>""", unsafe_allow_html=True)
        adviser = user.get("email","") if user else ""
        fn = cname.replace(" ", "_").replace("&", "and")
        ff_buf = build_factfind_doc(cname, adviser, "", ff_data or {}, client_facing=True)
        st.download_button(
            "Download Fact-Find (.docx)", data=ff_buf,
            file_name=f"Parafinix_{fn}_FactFind.docx",
            mime=DOCX_MIME, use_container_width=True, key="cp_dl_ff"
        )
    with gen_col2:
        st.markdown("""
        <div class="pfx-card" style="min-height:90px;border-left:4px solid #10B981;">
            <div style="font-weight:700;color:#0B1F3A;margin-bottom:4px;">Suitability + Compliance Report</div>
            <div style="font-size:0.82rem;color:#64748B;">
                Full AI-generated report pair, using saved client details.
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Generate Report →", type="primary", use_container_width=True, disabled=not ff_data):
            from core.fact_find import fact_find_to_notes
            st.session_state.page = "generate"
            st.session_state._prefill_notes = fact_find_to_notes(ff_data)
            st.rerun()
        if not ff_data:
            st.caption("Add client details above before generating a report.")

    st.markdown("---")

    cases = get_cases(cid)
    if not cases:
        st.info("No saved reports yet. Use 'Generate Report' above to create one.")
        return

    # ── Unsaved generation safety net ──
    held = st.session_state.get("_last_generation")
    if held:
        st.warning("You have an unsaved generation. Save it before navigating away or it will be lost.")
        fn = cname.replace(" ", "_").replace("&", "and")
        s1, s2, s3 = st.columns(3)
        with s1:
            suit = suitability_from_case({
                "report_part1": held["part1"], "report_part2": held["part2"],
                "adviser_name": held["adviser_name"], "firm_name": held["firm_name"],
                "basis": held["basis"], "charges": held["charges"], "report_ref": held["report_ref"],
            }, cname)
            st.download_button("Download Suitability", data=suit,
                file_name=f"Parafinix_{fn}_Suitability_UNSAVED.docx",
                mime=DOCX_MIME, use_container_width=True)
        with s2:
            comp = suitability_from_case({
                "report_part1": held["part1"], "report_part2": held["part2"],
                "adviser_name": held["adviser_name"], "firm_name": held["firm_name"],
                "basis": held["basis"], "charges": held["charges"], "report_ref": held["report_ref"],
            }, cname)
            st.download_button("Download Compliance", data=comp,
                file_name=f"Parafinix_{fn}_Compliance_UNSAVED.docx",
                mime=DOCX_MIME, use_container_width=True)
        with s3:
            if st.button("Discard unsaved", use_container_width=True):
                st.session_state.pop("_last_generation", None)
                st.rerun()
        st.markdown("---")

    st.markdown(f"#### {len(cases)} report{'s' if len(cases) != 1 else ''} saved")

    for idx, case in enumerate(cases):
        status = case.get("status", "draft")
        status_label, status_icon, _ = STATUS_LABELS.get(status, ("Draft", "🔵", "flag"))
        rag = case.get("rag_rating", "")
        rag_class = RAG_CLASS.get(rag, "")
        passes = case.get("passes", 0) or 0
        flags = case.get("flags", 0) or 0
        fails = case.get("fails", 0) or 0
        version = case.get("version", 1) or 1
        created = _format_date(case.get("created_at", ""))
        fn = cname.replace(" ", "_").replace("&", "and")
        safe_id = str(case["id"])[:8]

        with st.container():
            st.markdown(f"""
            <div class="folder-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="folder-name">{case.get('case_title','Report')}</div>
                        <div class="folder-meta">
                            Saved {created} &nbsp;·&nbsp;
                            <span class="{rag_class}">&#9679; {rag or '—'}</span> &nbsp;·&nbsp;
                            {status_icon} {status_label}
                        </div>
                        <div class="folder-meta" style="margin-top:4px;">
                            ✅ {passes} pass &nbsp; ⚠️ {flags} flag &nbsp; ❌ {fails} fail
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            a1, a2, a3, a4, a5 = st.columns([2, 2, 2, 2, 1])

            with a1:
                suit = suitability_from_case(case, cname)
                st.download_button("Suitability Report",
                    data=suit,
                    file_name=f"Parafinix_{fn}_v{version}_Suitability.docx",
                    mime=DOCX_MIME, use_container_width=True,
                    key=f"suit_{safe_id}_{idx}")

            with a2:
                comp = compliance_from_case(case, cname)
                st.download_button("Compliance Review",
                    data=comp,
                    file_name=f"Parafinix_{fn}_v{version}_Compliance.docx",
                    mime=DOCX_MIME, use_container_width=True,
                    key=f"comp_{safe_id}_{idx}")

            with a3:
                view_key = f"view_{safe_id}"
                if st.button("View report", use_container_width=True, key=f"viewbtn_{safe_id}_{idx}"):
                    current = st.session_state.get(view_key, False)
                    st.session_state[view_key] = not current
                    st.rerun()

            with a4:
                next_status = STATUS_FLOW.get(status)
                next_label = STATUS_NEXT_LABEL.get(status)
                if next_status and next_label:
                    if st.button(next_label, use_container_width=True, key=f"status_{safe_id}_{idx}"):
                        update_case_status(case["id"], next_status)
                        st.rerun()
                else:
                    st.caption("Signed off ✓")

            with a5:
                if st.button("Del", use_container_width=True, key=f"del_{safe_id}_{idx}"):
                    delete_case(case["id"])
                    st.rerun()

            if st.session_state.get(f"view_{safe_id}", False):
                with st.expander("Report content", expanded=True):
                    tab1, tab2 = st.tabs(["Suitability Report", "Compliance Findings"])
                    with tab1:
                        st.markdown(case.get("report_part1", ""))
                        st.markdown(case.get("report_part2", ""))
                    with tab2:
                        for line in (case.get("compliance_result", "") or "").split("\n"):
                            parts = line.split("|")
                            if "| PASS" in line and len(parts) >= 2:
                                st.markdown(f"<span class='pass'>PASS — {parts[0].strip()}</span>", unsafe_allow_html=True)
                            elif "| FLAG" in line and len(parts) >= 2:
                                note = parts[2].strip() if len(parts) > 2 else ""
                                st.markdown(f"<span class='flag'>FLAG — {parts[0].strip()}</span> · {note}", unsafe_allow_html=True)
                            elif "| FAIL" in line and len(parts) >= 2:
                                note = parts[2].strip() if len(parts) > 2 else ""
                                st.markdown(f"<span class='miss'>FAIL — {parts[0].strip()}</span> · {note}", unsafe_allow_html=True)

            st.markdown("---")