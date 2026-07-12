"""
ui/page_cases.py — Report history for a single client.

Every saved report appears as a card showing:
  - Title, version, date saved
  - RAG compliance rating
  - Status badge (Draft / In Review / Signed Off)
  - Download both docs (regenerated on demand)
  - View the report content in a reading pane
  - Change the status
  - Delete
"""
import streamlit as st
from datetime import datetime
from core.database import get_cases, delete_case, update_case_status
from documents.regenerate import suitability_from_case, compliance_from_case

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

    # ── Header ──
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(f"### {cname}")
        st.caption("Report history — every generated report is saved here. Download or track status any time.")
    with col_b:
        if st.button("← Back to clients", use_container_width=True):
            st.session_state.page = "clients"
            st.session_state.active_client_id = None
            st.session_state.active_client_name = None
            st.rerun()

    st.markdown("#### Start a new report")
    gen_col1, gen_col2, gen_col3 = st.columns(3)
    with gen_col1:
        st.markdown("""
        <div class="pfx-card" style="min-height:100px;">
            <div style="font-weight:700;color:#1F3346;margin-bottom:4px;">Quick Generate</div>
            <div style="font-size:0.82rem;color:#7A8A88;">Paste notes and go straight to full suitability report generation.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Quick Generate →", use_container_width=True):
            st.session_state.page = "generate"
            st.session_state.pop("_last_generation", None)
            st.session_state.pop("_prefill_notes", None)
            st.rerun()
    with gen_col2:
        st.markdown("""
        <div class="pfx-card" style="min-height:100px;border-left:4px solid #12B8A6;">
            <div style="font-weight:700;color:#1F3346;margin-bottom:4px;">Extract & Verify First ✦</div>
            <div style="font-size:0.82rem;color:#7A8A88;">AI structures your notes into editable fields. Then choose: generate report or download fact-find doc.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Extract & Verify →", use_container_width=True):
            st.session_state.page = "factfind"
            st.session_state.pop("_ff_data", None)
            st.session_state.pop("_show_ff_outputs", None)
            st.rerun()
    with gen_col3:
        st.markdown("""
        <div class="pfx-card" style="min-height:100px;border-left:4px solid #F5B841;">
            <div style="font-weight:700;color:#1F3346;margin-bottom:4px;">Generate Fact-Find Doc</div>
            <div style="font-size:0.82rem;color:#7A8A88;">Extract notes into a standalone fact-find document — client copy and internal gap analysis.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Fact-Find Doc →", use_container_width=True):
            st.session_state.page = "factfind"
            st.session_state.pop("_ff_data", None)
            st.session_state.pop("_show_ff_outputs", None)
            st.rerun()

    st.markdown("---")

    cases = get_cases(cid)
    if not cases:
        st.info("No saved reports yet. Click 'Generate new report' above to create one.")
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

        # ── Report card ──
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

            # Action row
            a1, a2, a3, a4, a5 = st.columns([2, 2, 2, 2, 1])

            # Download suitability
            with a1:
                suit = suitability_from_case(case, cname)
                st.download_button("Suitability Report",
                    data=suit,
                    file_name=f"Parafinix_{fn}_v{version}_Suitability.docx",
                    mime=DOCX_MIME, use_container_width=True,
                    key=f"suit_{safe_id}_{idx}")

            # Download compliance
            with a2:
                comp = compliance_from_case(case, cname)
                st.download_button("Compliance Review",
                    data=comp,
                    file_name=f"Parafinix_{fn}_v{version}_Compliance.docx",
                    mime=DOCX_MIME, use_container_width=True,
                    key=f"comp_{safe_id}_{idx}")

            # View report content
            with a3:
                view_key = f"view_{safe_id}"
                if st.button("View report", use_container_width=True, key=f"viewbtn_{safe_id}_{idx}"):
                    current = st.session_state.get(view_key, False)
                    st.session_state[view_key] = not current
                    st.rerun()

            # Status advance
            with a4:
                next_status = STATUS_FLOW.get(status)
                next_label = STATUS_NEXT_LABEL.get(status)
                if next_status and next_label:
                    if st.button(next_label, use_container_width=True, key=f"status_{safe_id}_{idx}"):
                        update_case_status(case["id"], next_status)
                        st.rerun()
                else:
                    st.caption("Signed off ✓")

            # Delete
            with a5:
                if st.button("Del", use_container_width=True, key=f"del_{safe_id}_{idx}"):
                    delete_case(case["id"])
                    st.rerun()

            # Inline view pane (toggled by View button)
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
