"""
ui/page_generate.py — Report generator with all inputs on the main page.
No sidebar dependency — everything is visible on the main canvas.
"""
import streamlit as st
from datetime import date
from core.ai_client import call_drafting_model, call_compliance_model
from core.preflight import run_preflight
from core.ai_prompts import (
    SYSTEM_PROMPT, FULL_REPORT_PROMPT, PASS2_PROMPT, PASS3_PROMPT, PASS4_PROMPT,
    TEMPLATE_PROMPT, COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS,
)
from core.database import save_case, get_next_version
from documents.suitability_doc import build_suitability_doc
from documents.compliance_doc import build_compliance_doc
from documents.template_reader import extract_template_structure

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _rag(passes, flags, fails):
    if fails > 2:
        return "RED", "miss", "Not ready for issue — critical items must be resolved"
    elif flags > 5 or fails > 0:
        return "AMBER", "flag", "Further work required before issue"
    return "GREEN", "pass", "Ready for adviser sign-off"


def _run_generation(cname, adviser_name, firm_name, basis, charges, report_ref, notes, template_text):
    progress = st.progress(0)
    status = st.empty()

    if template_text:
        p1_msg = (
            f"Client: {cname}\nAdviser: {adviser_name}\nFirm: {firm_name}\n"
            f"Basis: {basis}\nCharges: {charges}\n\nNOTES:\n{notes}\n\n"
            f"{TEMPLATE_PROMPT.format(template_text=template_text[:3000])}\n\n"
            f"Write the first half following the template. Use markdown tables."
        )
    else:
        p1_msg = (
            f"Client: {cname}\nAdviser: {adviser_name}\nFirm: {firm_name}\n"
            f"Basis: {basis}\nCharges: {charges}\n\nNOTES:\n{notes}\n\n{FULL_REPORT_PROMPT}"
        )

    status.write("Pass 1 of 4 — drafting circumstances, objectives, risk...")
    progress.progress(12)
    part1 = call_drafting_model(SYSTEM_PROMPT, p1_msg, max_tokens=8000)
    progress.progress(28)

    status.write("Pass 2 of 4 — first recommendations...")
    p2_msg = (
        f"Client: {cname}\nAdviser: {adviser_name}\nFirm: {firm_name}\n\n"
        f"NOTES:\n{notes}\n\nSECTIONS 1-5:\n{part1[:3000]}\n\n{PASS2_PROMPT}"
    )
    part2 = call_drafting_model(SYSTEM_PROMPT, p2_msg, max_tokens=6000)
    progress.progress(46)

    status.write("Pass 3 of 4 — remaining recommendations...")
    p3_msg = (
        f"Client: {cname}\nAdviser: {adviser_name}\nFirm: {firm_name}\n\n"
        f"NOTES:\n{notes}\n\nSECTIONS 1-6 (FIRST HALF):\n{part2[:3000]}\n\n{PASS3_PROMPT}"
    )
    part3 = call_drafting_model(SYSTEM_PROMPT, p3_msg, max_tokens=6000)
    progress.progress(64)

    status.write("Pass 4 of 4 — costs, tax, risks, next steps...")
    recs_so_far = part2 + "\n\n" + part3
    p4_msg = (
        f"Client: {cname}\nAdviser: {adviser_name}\nFirm: {firm_name}\n\n"
        f"NOTES:\n{notes}\n\nALL RECOMMENDATIONS SO FAR:\n{recs_so_far[:3000]}\n\n{PASS4_PROMPT}"
    )
    part4 = call_drafting_model(SYSTEM_PROMPT, p4_msg, max_tokens=6000)
    progress.progress(80)

    status.write("Running 28-point compliance review...")
    combined = part1 + "\n\n" + part2 + "\n\n" + part3 + "\n\n" + part4
    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined[:7000]}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=2500,
    )
    progress.progress(100)
    status.empty()

    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)

    return {
        "part1": part1, "part2": part2, "part3": part3, "part4": part4,
        "check_text": check_text,
        "passes": passes, "flags": flags, "fails": fails,
        "firm_name": firm_name, "adviser_name": adviser_name,
        "basis": basis, "charges": charges, "report_ref": report_ref,
        "notes": notes,
    }
def render_generate_page():
    user = st.session_state.user
    cid  = st.session_state.active_client_id
    cname = st.session_state.active_client_name

    # ── Header ──
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(f"### New report for {cname}")
    with col_b:
        if st.button("← Back to client", use_container_width=True):
            st.session_state.page = "cases"
            st.session_state.pop("_last_generation", None)
            st.rerun()

    st.markdown("---")

    # ── If we already have a result held in session, show it ──
    result = st.session_state.get("_last_generation")
    if result:
        _show_result(user, cid, cname, result)
        st.markdown("---")
        if st.button("Generate a new report instead", use_container_width=False):
            st.session_state.pop("_last_generation", None)
            st.rerun()
        return

    # ── Input form — all on main page ──
    st.markdown("#### Report details")
    c1, c2 = st.columns(2)
    with c1:
        firm_name    = st.text_input("Firm name", placeholder="e.g. Oakfield Wealth Management")
        adviser_name = st.text_input("Adviser name", placeholder="e.g. Sarah Chen")
        report_ref   = st.text_input("Report reference", placeholder="e.g. OW-2026-001")
    with c2:
        basis   = st.selectbox("Basis of advice",
            ["Independent", "Restricted — whole of market", "Restricted — limited panel"])
        charges = st.text_area("Adviser charges",
            placeholder="e.g. Initial: 1% of funds. Ongoing: 0.5% p.a.", height=100)

    st.markdown("---")
    st.markdown("#### Firm template *(optional)*")
    st.caption("Upload your firm's own Word template and the AI will follow your exact headings and structure.")
    template_file = st.file_uploader("Upload .docx template", type=["docx"])
    template_text = ""
    if template_file:
        template_text, _ = extract_template_structure(template_file)
        if template_text:
            st.success(f"Template loaded — {len(template_text.split(chr(10)))} lines extracted")
        else:
            st.error("Could not read that template file.")

    st.markdown("---")
    st.markdown("#### Meeting notes / fact-find")
    st.caption("Paste the full fact-find or meeting notes. The more detail you provide, the better the report.")
    # Pre-fill from fact-find extraction if it came through that flow
    prefill = st.session_state.pop("_prefill_notes", None) or ""
    notes = st.text_area("", height=320,
        value=prefill,
        placeholder="Paste all meeting notes here...\n\nInclude: client details, income, assets, pensions, protection, objectives, risk profile, adviser notes.")
    if prefill:
        st.success("Structured fact-find data pre-loaded from extraction. Review above then click Generate Report.")

    st.markdown("---")
    gen = st.button("Generate Report", type="primary", use_container_width=True)

    if gen:
        if not notes.strip():
            st.error("Please paste meeting notes before generating.")
            return
        # ── PRE-FLIGHT CHECK ──────────────────────────────────
        # Skip pre-flight if notes came from Extract & Verify (already verified)
        # or if user already confirmed pre-flight this session
        is_prefilled   = bool(st.session_state.get("_prefill_notes", ""))
        already_confirmed = st.session_state.get("_preflight_confirmed", False)

        skip_always = st.session_state.get("_skip_preflight", False)
        if not is_prefilled and not already_confirmed and not skip_always:
            with st.spinner("Running pre-flight check on your notes..."):
                pf = run_preflight(notes)
            st.session_state._preflight_result = pf
            st.session_state._pending_notes    = notes
            st.session_state._pending_params   = {
                "adviser_name": adviser_name, "firm_name": firm_name,
                "basis": basis, "charges": charges, "report_ref": report_ref,
            }
            st.rerun()
        else:
            # Pre-flight already confirmed — go straight to generation
            st.session_state.pop("_preflight_confirmed", None)
            result = _run_generation(
                cname, adviser_name, firm_name, basis, charges, report_ref, notes, template_text
            )
            st.session_state._last_generation = result
            st.session_state.pop("_pending_notes", None)
            st.session_state.pop("_preflight_result", None)
            st.rerun()

    # ── SHOW PRE-FLIGHT RESULT (if triggered) ──────────────────
    pf = st.session_state.get("_preflight_result")
    if pf and not st.session_state.get("_last_generation"):
        _show_preflight(pf, cname)


def _show_preflight(pf: dict, cname: str):
    """
    Renders the pre-flight confirmation screen between notes input
    and report generation. Shows what was found, what is missing,
    and gives the user the choice to proceed or go back.
    """
    confidence = pf.get("confidence", "medium")
    ready      = pf.get("ready_to_generate", True)
    found      = pf.get("found", [])
    critical   = pf.get("missing_critical", [])
    minor      = pf.get("missing_minor", [])
    unclear    = pf.get("unclear", [])
    rec        = pf.get("recommendation", "")
    parse_err  = pf.get("_parse_error", False)

    conf_color = {"high": "pass", "medium": "flag", "low": "miss"}.get(confidence, "flag")
    conf_icon  = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(confidence, "🟡")

    st.markdown("---")
    st.markdown("#### Pre-flight check")
    st.caption(
        "Before generating the full report, I checked your notes for completeness. "
        "Review the findings below and decide whether to proceed."
    )

    if parse_err:
        st.info("Pre-flight scan completed — proceeding with generation.")
    else:
        # Confidence card
        st.markdown(
            f"""<div style='background:{"#EAF4EE" if confidence=="high" else "#FEF9E7" if confidence=="medium" else "#FDECEA"};
            border-radius:10px;padding:14px 18px;margin-bottom:16px;
            border:1px solid {"#C9DED2" if confidence=="high" else "#F5CBA7" if confidence=="medium" else "#F1948A"};'>
            <div style='font-size:1.05rem;font-weight:700;color:#1F3346;'>
                {conf_icon} Notes quality: <span class='{conf_color}'>{confidence.upper()}</span>
            </div>
            <div style='font-size:0.88rem;color:#5B6B79;margin-top:4px;'>{rec}</div>
            </div>""",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:
            if found:
                st.markdown("**Found in your notes**")
                for item in found:
                    st.markdown(
                        f"<span class='pass'>✅ {item}</span>",
                        unsafe_allow_html=True
                    )
            if unclear:
                st.markdown("**Present but unclear**")
                for item in unclear:
                    st.markdown(
                        f"<span class='flag'>⚠️ {item}</span>",
                        unsafe_allow_html=True
                    )

        with col2:
            if critical:
                st.markdown("**Critical items missing**")
                for item in critical:
                    st.markdown(
                        f"<span class='miss'>❌ {item}</span>",
                        unsafe_allow_html=True
                    )
            if minor:
                st.markdown("**Minor items missing**")
                for item in minor:
                    st.markdown(
                        f"<div style='color:#7A8A88;font-size:0.88rem;'>• {item}</div>",
                        unsafe_allow_html=True
                    )

    st.markdown("---")

    if critical and not ready:
        st.warning(
            f"There are {len(critical)} critical item(s) missing. "
            "The report will contain significant [MISSING] gaps. "
            "Consider going back to add this information before generating."
        )

    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button("← Go back and add more detail", use_container_width=True, key="pf_back"):
            st.session_state.pop("_preflight_result", None)
            st.session_state.pop("_pending_notes", None)
            st.session_state.pop("_pending_params", None)
            st.rerun()
    with btn2:
        label = "Generate Report" if not critical else "Generate anyway (with gaps)"
        btn_type = "primary" if not critical else "secondary"
        if st.button(label, type=btn_type, use_container_width=True, key="pf_generate"):
            st.session_state._preflight_confirmed = True
            st.session_state.pop("_preflight_result", None)
            st.rerun()
    with btn3:
        if st.button("Skip pre-flight in future", use_container_width=True, key="pf_skip"):
            st.session_state._skip_preflight = True
            st.session_state._preflight_confirmed = True
            st.session_state.pop("_preflight_result", None)
            st.rerun()


def _show_result(user, cid, cname, result):
    """Renders the clean result card — no full report text dump."""
    rag, rag_class, rag_msg = _rag(result["passes"], result["flags"], result["fails"])
    fn = cname.replace(" ", "_").replace("&", "and")

    # Summary card
    st.markdown("#### Report generated successfully")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compliance", rag)
    c2.metric("Pass", result["passes"])
    c3.metric("Flag", result["flags"])
    c4.metric("Fail", result["fails"])
    st.markdown(
        f"<div style='padding:10px 0 4px 0;'>"
        f"<span class='{rag_class}' style='font-size:0.95rem;'>● {rag_msg}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Two document blocks
    st.markdown("#### Download documents")
    doc1, doc2 = st.columns(2)

    with doc1:
        st.markdown("""
        <div class="pfx-card">
            <div style="font-weight:700;color:#1F3346;font-size:1rem;margin-bottom:6px;">
                Suitability Report
            </div>
            <div style="font-size:0.82rem;color:#7A8A88;margin-bottom:14px;">
                Full client-ready suitability report — all 11 sections
            </div>
        </div>
        """, unsafe_allow_html=True)
        suit = build_suitability_doc(
            cname, result["adviser_name"], result["firm_name"],
            result["basis"], result["charges"], result["report_ref"],
            result["part1"], result["part2"],
            result.get("part3", ""), result.get("part4", "")
        )
        st.download_button(
            "Download Suitability Report (.docx)",
            data=suit,
            file_name=f"Parafinix_{fn}_Suitability_{date.today().strftime('%d%b%Y')}.docx",
            mime=DOCX_MIME, use_container_width=True, key="dl_suit"
        )

    with doc2:
        st.markdown("""
        <div class="pfx-card">
            <div style="font-weight:700;color:#1F3346;font-size:1rem;margin-bottom:6px;">
                Compliance Review
            </div>
            <div style="font-size:0.82rem;color:#7A8A88;margin-bottom:14px;">
                Separate compliance document — RAG rating, 28-point COBS 9A check, sign-off page
            </div>
        </div>
        """, unsafe_allow_html=True)
        comp = build_compliance_doc(
            cname, result["adviser_name"], result["firm_name"],
            result["report_ref"], result["check_text"],
            result["passes"], result["flags"], result["fails"]
        )
        st.download_button(
            "Download Compliance Review (.docx)",
            data=comp,
            file_name=f"Parafinix_{fn}_Compliance_{date.today().strftime('%d%b%Y')}.docx",
            mime=DOCX_MIME, use_container_width=True, key="dl_comp"
        )

    st.markdown("---")

    # Preview expanders (collapsed by default — clean, not a wall of text)
    with st.expander("Preview report content", expanded=False):
        tab_a, tab_b, tab_c, tab_d = st.tabs(["Sections 1-5", "Recommendations (1st half)", "Recommendations (2nd half)", "Sections 7-11 + Checks"])
        with tab_a: st.markdown(result["part1"])
        with tab_b: st.markdown(result["part2"])
        with tab_c: st.markdown(result.get("part3", ""))
        with tab_d: st.markdown(result.get("part4", ""))

    with st.expander("Preview compliance findings", expanded=False):
        for line in result["check_text"].split("\n"):
            parts = line.split("|")
            if "| PASS" in line and len(parts) >= 2:
                st.markdown(f"<span class='pass'>✅ PASS — {parts[0].strip()}</span>", unsafe_allow_html=True)
            elif "| FLAG" in line and len(parts) >= 2:
                note = parts[2].strip() if len(parts) > 2 else ""
                st.markdown(f"<span class='flag'>⚠️ FLAG — {parts[0].strip()}</span> · {note}", unsafe_allow_html=True)
            elif "| FAIL" in line and len(parts) >= 2:
                note = parts[2].strip() if len(parts) > 2 else ""
                st.markdown(f"<span class='miss'>❌ FAIL — {parts[0].strip()}</span> · {note}", unsafe_allow_html=True)

    st.markdown("---")

    # Save block
    st.markdown("#### Save to client folder")
    st.caption("Save this report so you can download it again or track its status any time you log in. Nothing is lost.")
    save_col1, save_col2 = st.columns([3, 1])
    with save_col2:
        if st.button("Save to folder", type="primary", use_container_width=True):
            version = get_next_version(cid)
            title   = f"Report v{version} — {date.today().strftime('%d %b %Y')}"
            saved   = save_case(
                user_id=user["id"], client_id=cid, case_title=title,
                fact_find=result["notes"],
                part1=result["part1"], part2=result["part2"],
                part3=result.get("part3", ""), part4=result.get("part4", ""),
                compliance=result["check_text"], rag_rating=rag,
                passes=result["passes"], flags=result["flags"], fails=result["fails"],
                firm_name=result["firm_name"], adviser_name=result["adviser_name"],
                basis=result["basis"], charges=result["charges"],
                report_ref=result["report_ref"], status="draft", version=version,
            )
            if saved:
                st.success("Saved to client folder.")
                st.session_state.pop("_last_generation", None)
                st.session_state.page = "cases"
                st.rerun()
