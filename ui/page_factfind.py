"""
ui/page_factfind.py — Fact-find extraction and review screen.

Flow:
1. Paste raw meeting notes
2. AI extracts structured data (60+ fields across 10 categories)
3. Every field appears as an editable text box
4. AI flags are shown at the top — items missing or needing confirmation
5. Paraplanner edits, confirms, then generates the report from clean data
"""
import streamlit as st
import json
from core.fact_find import extract_fact_find, fact_find_to_notes
from core.database import update_client_fact_find, get_client_by_id

def _field(label: str, value: str, key: str, height: int = None) -> str:
    """Renders an editable input and returns the current value."""
    placeholder = "Not found in notes"
    if height:
        return st.text_area(label, value=value or "", key=key,
                            placeholder=placeholder, height=height)
    return st.text_input(label, value=value or "", key=key,
                         placeholder=placeholder)

def _section(title: str, icon: str = ""):
    st.markdown(f"#### {icon} {title}" if icon else f"#### {title}")
    st.markdown("<hr style='margin:4px 0 14px 0;border-color:#E4EBEA;'>", unsafe_allow_html=True)


def render_factfind_page():
    user = st.session_state.user
    cid   = st.session_state.active_client_id
    cname = st.session_state.active_client_name

    # ── Header ──
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(f"### Extract & Verify — {cname}")
        st.caption("AI extracts your notes into structured fields. Review, edit, then generate.")
    with col_b:
        if st.button("← Back to client", use_container_width=True):
            st.session_state.page = "cases"
            st.session_state.pop("_ff_data", None)
            st.session_state.pop("_ff_notes", None)
            st.rerun()

    st.markdown("---")

    # Auto-load saved details if this client already has them
    if "_ff_data" not in st.session_state:
        client_record = get_client_by_id(cid)
        if client_record.get("fact_find_data"):
            st.session_state._ff_data = client_record["fact_find_data"]
            st.session_state._ff_notes = client_record.get("fact_find_notes", "")

    # ── STEP 1: input — PDF upload OR paste notes ──
    if not st.session_state.get("_ff_data"):
        st.markdown("#### Step 1 — Provide client information")
        st.caption(
            "Upload PDFs (fact-finds, pension statements, provider letters) "
            "and/or paste meeting notes. The AI extracts ~60 fields from whatever you provide."
        )

        tab_pdf, tab_text, tab_both = st.tabs([
            "Upload PDF(s)",
            "Paste notes",
            "Upload PDFs and paste notes",
        ])

        pdf_text    = ""
        manual_text = ""
        pdf_summary = None

        with tab_pdf:
            st.caption(
                "Upload one or more PDFs — fact-finds, pension statements, annual review reports, "
                "meeting notes exported from a dictation tool. Works best with typed/digital PDFs. "
                "Scanned or handwritten documents cannot be read automatically."
            )
            uploaded_files = st.file_uploader(
                "Upload PDF file(s)",
                type=["pdf"],
                accept_multiple_files=True,
                key="ff_pdf_upload",
                help="You can upload multiple PDFs — e.g. a fact-find plus a pension statement."
            )
            if uploaded_files:
                with st.spinner(f"Reading {len(uploaded_files)} PDF file(s)..."):
                    pdf_text, pdf_summary = extract_text_from_multiple_pdfs(uploaded_files)

                if pdf_summary:
                    for f_info in pdf_summary["files"]:
                        status = "✅" if f_info["extracted"] else "⚠️"
                        st.write(f"{status} **{f_info['name']}** — {f_info['pages']} page(s)")
                    if pdf_summary["warnings"]:
                        for w in pdf_summary["warnings"]:
                            st.warning(w)
                    if pdf_text.strip():
                        with st.expander("Preview extracted text", expanded=False):
                            st.text(pdf_text[:2000] + ("..." if len(pdf_text) > 2000 else ""))

        with tab_text:
            st.caption("Paste raw meeting notes, bullet points, shorthand — anything. The AI will structure it.")
            manual_text = st.text_area(
                "",
                height=300,
                placeholder="Paste meeting notes here... Include: client details, income, pensions, protection, objectives, risk, adviser notes.",
                key="ff_manual_text"
            )

        with tab_both:
            st.caption("Upload PDFs first, then add any additional notes from the meeting that aren't in the PDFs.")
            uploaded_files_b = st.file_uploader(
                "Upload PDF file(s)",
                type=["pdf"],
                accept_multiple_files=True,
                key="ff_pdf_upload_b",
            )
            if uploaded_files_b:
                with st.spinner(f"Reading {len(uploaded_files_b)} PDF file(s)..."):
                    pdf_text_b, pdf_summary_b = extract_text_from_multiple_pdfs(uploaded_files_b)
                if pdf_text_b.strip():
                    pdf_text = pdf_text_b
                    for f_info in pdf_summary_b["files"]:
                        status = "✅" if f_info["extracted"] else "⚠️"
                        st.write(f"{status} **{f_info['name']}** — {f_info['pages']} page(s)")
                if pdf_summary_b and pdf_summary_b["warnings"]:
                    for w in pdf_summary_b["warnings"]:
                        st.warning(w)

            additional_notes = st.text_area(
                "Additional meeting notes",
                height=200,
                placeholder="Any details not in the PDFs — verbal confirmations, updated figures, new objectives discussed in the meeting...",
                key="ff_additional_notes"
            )
            if additional_notes.strip():
                manual_text = additional_notes

        combined_input = ""
        if pdf_text.strip():
            combined_input += pdf_text.strip()
        if manual_text.strip():
            sep = "\n\n" if combined_input else ""
            combined_input += sep + "ADDITIONAL NOTES:\n" + manual_text.strip()

        st.markdown("---")
        c_info, c_btn = st.columns([3, 1])
        with c_info:
            if combined_input:
                word_count = len(combined_input.split())
                st.caption(f"Ready to extract: {word_count:,} words of input from your sources.")
            else:
                st.caption("Upload a PDF or paste notes above, then click Extract.")
        with c_btn:
            extract_btn = st.button(
                "Extract Fact-Find",
                type="primary",
                use_container_width=True,
                disabled=not bool(combined_input.strip())
            )

        if extract_btn:
            if not combined_input.strip():
                st.error("Please upload a PDF or paste notes before extracting.")
                return
            with st.spinner("AI is extracting structured data from your sources..."):
                data = extract_fact_find(combined_input)
            if data is None:
                st.error("Extraction failed — please try again or check your input.")
                return
            st.session_state._ff_data = data
            st.session_state._ff_notes = combined_input
            update_client_fact_find(cid, data, combined_input)
            st.rerun()
        return

    # ── STEP 2: review and edit extracted data ──
    data = st.session_state._ff_data

    flags = [f for f in data.get("flags", []) if f and f.strip()]
    if flags:
        st.markdown("#### ⚠️ Items to check before generating")
        st.markdown(
            "<div style='background:#FEF9E7;border:1px solid #F5CBA7;border-radius:10px;padding:16px 18px;margin-bottom:20px;'>"
            + "".join(f"<div style='color:#8A6A1F;margin-bottom:6px;'>• {fl}</div>" for fl in flags)
            + "</div>",
            unsafe_allow_html=True
        )

    st.markdown("#### Step 2 — Review and correct the extracted data")
    st.caption("Every field is editable. Correct anything the AI got wrong or missed. Empty fields were not found in your notes.")
    st.markdown("")

    _section("Personal Details", "👤")
    p = data.get("personal", {})
    c1, c2 = st.columns(2)
    with c1:
        p["client1_name"] = _field("Client 1 name", p.get("client1_name"), "ff_c1_name")
        p["client1_dob"]  = _field("Client 1 date of birth", p.get("client1_dob"), "ff_c1_dob")
        p["client1_employment"] = _field("Client 1 employment", p.get("client1_employment"), "ff_c1_emp")
        p["client1_employer"]   = _field("Client 1 employer", p.get("client1_employer"), "ff_c1_er")
    with c2:
        p["client2_name"] = _field("Client 2 name (if applicable)", p.get("client2_name"), "ff_c2_name")
        p["client2_dob"]  = _field("Client 2 date of birth", p.get("client2_dob"), "ff_c2_dob")
        p["client2_employment"] = _field("Client 2 employment", p.get("client2_employment"), "ff_c2_emp")
        p["client2_employer"]   = _field("Client 2 employer", p.get("client2_employer"), "ff_c2_er")
    p["address"]        = _field("Address", p.get("address"), "ff_addr")
    p["marital_status"] = _field("Marital status", p.get("marital_status"), "ff_marital")

    st.markdown("**Dependants**")
    deps = p.get("dependants", [{}])
    if not deps:
        deps = [{}]
    new_deps = []
    for i, d in enumerate(deps):
        dc1, dc2, dc3 = st.columns(3)
        with dc1: name = st.text_input("Name", value=d.get("name",""), key=f"ff_dep_name_{i}", placeholder="e.g. Emily")
        with dc2: age  = st.text_input("Age",  value=d.get("age",""),  key=f"ff_dep_age_{i}",  placeholder="e.g. 12")
        with dc3: rel  = st.text_input("Relationship", value=d.get("relationship",""), key=f"ff_dep_rel_{i}", placeholder="e.g. Daughter")
        new_deps.append({"name": name, "age": age, "relationship": rel})
    if st.button("Add dependant", key="ff_add_dep"):
        new_deps.append({"name":"","age":"","relationship":""})
    p["dependants"] = new_deps
    data["personal"] = p

    st.markdown("")

    _section("Income", "💷")
    inc = data.get("income", {})
    c1, c2 = st.columns(2)
    with c1:
        inc["client1_gross_salary"] = _field("Client 1 gross salary (pa)", inc.get("client1_gross_salary"), "ff_c1_gross")
        inc["client1_net_monthly"]  = _field("Client 1 net monthly",        inc.get("client1_net_monthly"),  "ff_c1_net")
        inc["client1_bonus"]        = _field("Client 1 bonus",              inc.get("client1_bonus"),        "ff_c1_bon")
    with c2:
        inc["client2_gross_salary"] = _field("Client 2 gross salary (pa)", inc.get("client2_gross_salary"), "ff_c2_gross")
        inc["client2_net_monthly"]  = _field("Client 2 net monthly",        inc.get("client2_net_monthly"),  "ff_c2_net")
        inc["client2_bonus"]        = _field("Client 2 bonus",              inc.get("client2_bonus"),        "ff_c2_bon")
    inc["other_income"]    = _field("Other income",    inc.get("other_income"),    "ff_other_inc")
    inc["salary_sacrifice"]= _field("Salary sacrifice", inc.get("salary_sacrifice"),"ff_sal_sac")
    inc["monthly_surplus"] = _field("Monthly surplus",  inc.get("monthly_surplus"), "ff_surplus")
    data["income"] = inc

    exp = data.get("expenditure", {})
    c1, c2 = st.columns(2)
    with c1: exp["mortgage_payment"] = _field("Mortgage/rent payment pm", exp.get("mortgage_payment"), "ff_mort_pay")
    with c2: exp["total_monthly"]    = _field("Total monthly expenditure",  exp.get("total_monthly"),    "ff_total_exp")
    exp["notes"] = _field("Expenditure notes", exp.get("notes"), "ff_exp_notes")
    data["expenditure"] = exp

    st.markdown("")

    _section("Assets & Savings", "🏦")
    assets = data.get("assets", {})
    c1, c2, c3 = st.columns(3)
    with c1: assets["property_value"]  = _field("Property value",   assets.get("property_value"),  "ff_prop_val")
    with c2: assets["mortgage_balance"]= _field("Mortgage balance", assets.get("mortgage_balance"),"ff_mort_bal")
    with c3: assets["property_equity"] = _field("Property equity",  assets.get("property_equity"), "ff_prop_eq")
    assets["premium_bonds"] = _field("Premium Bonds", assets.get("premium_bonds"), "ff_prem_bonds")

    st.markdown("**Cash savings**")
    savings = assets.get("cash_savings", [{}])
    new_savings = []
    for i, s in enumerate(savings):
        sc1, sc2, sc3 = st.columns(3)
        with sc1: prov = st.text_input("Provider", value=s.get("provider",""), key=f"ff_sav_prov_{i}")
        with sc2: typ  = st.text_input("Type",     value=s.get("type",""),     key=f"ff_sav_type_{i}", placeholder="e.g. Easy Access")
        with sc3: val  = st.text_input("Value",    value=s.get("value",""),    key=f"ff_sav_val_{i}")
        new_savings.append({"provider": prov, "type": typ, "value": val})
    if st.button("Add savings account", key="ff_add_sav"):
        new_savings.append({"provider":"","type":"","value":""})
    assets["cash_savings"] = new_savings

    st.markdown("**ISAs**")
    isas = assets.get("isas", [{}])
    new_isas = []
    for i, isa in enumerate(isas):
        ic1, ic2, ic3, ic4 = st.columns(4)
        with ic1: prov  = st.text_input("Provider", value=isa.get("provider",""),     key=f"ff_isa_prov_{i}")
        with ic2: typ   = st.text_input("Type",     value=isa.get("type",""),         key=f"ff_isa_type_{i}", placeholder="Cash/S&S")
        with ic3: val   = st.text_input("Value",    value=isa.get("value",""),        key=f"ff_isa_val_{i}")
        with ic4: contr = st.text_input("Contributions", value=isa.get("contributions",""), key=f"ff_isa_contr_{i}")
        new_isas.append({"provider": prov, "type": typ, "value": val, "contributions": contr})
    if st.button("Add ISA", key="ff_add_isa"):
        new_isas.append({"provider":"","type":"","value":"","contributions":""})
    assets["isas"] = new_isas

    st.markdown("**General Investment Accounts (GIA)**")
    gias = assets.get("gia", [{}])
    new_gias = []
    for i, g in enumerate(gias):
        gc1, gc2 = st.columns(2)
        with gc1: prov = st.text_input("Provider", value=g.get("provider",""), key=f"ff_gia_prov_{i}")
        with gc2: val  = st.text_input("Value",    value=g.get("value",""),    key=f"ff_gia_val_{i}")
        new_gias.append({"provider": prov, "value": val})
    if st.button("Add GIA", key="ff_add_gia"):
        new_gias.append({"provider":"","value":""})
    assets["gia"] = new_gias
    data["assets"] = assets

    st.markdown("")

    _section("Pensions", "🏛️")
    pensions = data.get("pensions", [{}])
    new_pensions = []
    for i, pen in enumerate(pensions):
        st.markdown(f"**Pension {i+1}**")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            prov  = st.text_input("Provider",    value=pen.get("provider",""),    key=f"ff_pen_prov_{i}")
            typ   = st.text_input("Type",        value=pen.get("type",""),        key=f"ff_pen_type_{i}", placeholder="DC/DB/SIPP")
            val   = st.text_input("Current value", value=pen.get("current_value",""), key=f"ff_pen_val_{i}")
        with pc2:
            ee  = st.text_input("Employee contribution", value=pen.get("employee_contribution",""), key=f"ff_pen_ee_{i}")
            er  = st.text_input("Employer contribution", value=pen.get("employer_contribution",""), key=f"ff_pen_er_{i}")
            fund= st.text_input("Fund name", value=pen.get("fund_name",""), key=f"ff_pen_fund_{i}")
        with pc3:
            ret_age = st.text_input("Selected retirement age", value=pen.get("selected_retirement_age",""), key=f"ff_pen_age_{i}")
            status  = st.text_input("Status", value=pen.get("status",""), key=f"ff_pen_status_{i}", placeholder="Active/Paid-up")
            notes   = st.text_input("Notes",  value=pen.get("notes",""),  key=f"ff_pen_notes_{i}")
        new_pensions.append({"provider":prov,"type":typ,"current_value":val,
                             "employee_contribution":ee,"employer_contribution":er,
                             "fund_name":fund,"selected_retirement_age":ret_age,
                             "status":status,"notes":notes})
    if st.button("Add pension", key="ff_add_pen"):
        new_pensions.append({k:"" for k in ["provider","type","current_value","employee_contribution","employer_contribution","fund_name","selected_retirement_age","status","notes"]})
    data["pensions"] = new_pensions

    st.markdown("")

    _section("Protection", "🛡️")
    prots = data.get("protection", [{}])
    new_prots = []
    for i, pol in enumerate(prots):
        st.markdown(f"**Policy {i+1}**")
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            typ  = st.text_input("Type",     value=pol.get("type",""),     key=f"ff_pol_type_{i}", placeholder="Life/IP/CI")
            prov = st.text_input("Provider", value=pol.get("provider",""), key=f"ff_pol_prov_{i}")
        with rc2:
            ben  = st.text_input("Benefit",  value=pol.get("benefit",""),  key=f"ff_pol_ben_{i}")
            prem = st.text_input("Premium",  value=pol.get("premium",""),  key=f"ff_pol_prem_{i}")
        with rc3:
            term  = st.text_input("Term",  value=pol.get("term",""),  key=f"ff_pol_term_{i}")
            basis = st.text_input("Basis", value=pol.get("basis",""), key=f"ff_pol_basis_{i}", placeholder="Single/Joint")
        notes = st.text_input("Notes", value=pol.get("notes",""), key=f"ff_pol_notes_{i}")
        new_prots.append({"type":typ,"provider":prov,"benefit":ben,"premium":prem,"term":term,"basis":basis,"notes":notes})
    if st.button("Add policy", key="ff_add_pol"):
        new_prots.append({k:"" for k in ["type","provider","benefit","premium","term","basis","notes"]})
    data["protection"] = new_prots

    st.markdown("")

    _section("Liabilities", "🏠")
    liab = data.get("liabilities", {})
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        liab["mortgage_balance"] = _field("Mortgage balance", liab.get("mortgage_balance"), "ff_liab_bal")
        liab["mortgage_rate"]    = _field("Interest rate",    liab.get("mortgage_rate"),    "ff_liab_rate")
    with lc2:
        liab["mortgage_term"]    = _field("Remaining term",   liab.get("mortgage_term"),    "ff_liab_term")
        liab["mortgage_monthly"] = _field("Monthly payment",  liab.get("mortgage_monthly"), "ff_liab_pay")
    with lc3:
        liab["other_loans"]  = _field("Other loans",   liab.get("other_loans"),  "ff_liab_loans")
        liab["credit_cards"] = _field("Credit cards",  liab.get("credit_cards"), "ff_liab_cc")
    data["liabilities"] = liab

    st.markdown("")

    _section("Objectives", "🎯")
    obj = data.get("objectives", {})
    obj["primary_objective"] = _field("Primary objective", obj.get("primary_objective"), "ff_obj_primary", height=80)
    oc1, oc2 = st.columns(2)
    with oc1:
        obj["target_retirement_age_client1"] = _field("Target retirement age (Client 1)", obj.get("target_retirement_age_client1"), "ff_obj_ret1")
        obj["target_retirement_income"]      = _field("Target retirement income",         obj.get("target_retirement_income"),      "ff_obj_inc")
    with oc2:
        obj["target_retirement_age_client2"] = _field("Target retirement age (Client 2)", obj.get("target_retirement_age_client2"), "ff_obj_ret2")
        obj["time_horizons"]                 = _field("Time horizons",                    obj.get("time_horizons"),                 "ff_obj_time")
    obj["secondary_objectives"] = _field("Secondary objectives", obj.get("secondary_objectives"), "ff_obj_sec", height=80)
    obj["priorities"]           = _field("Priorities",           obj.get("priorities"),           "ff_obj_pri", height=60)
    obj["concerns"]             = _field("Concerns / main worries", obj.get("concerns"),           "ff_obj_con", height=60)
    data["objectives"] = obj

    st.markdown("")

    _section("Attitude to Risk & Capacity for Loss", "📊")
    risk = data.get("risk", {})
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        risk["questionnaire_tool"]  = _field("Questionnaire tool", risk.get("questionnaire_tool"),  "ff_risk_tool", )
        risk["questionnaire_score"] = _field("Score",              risk.get("questionnaire_score"), "ff_risk_score")
    with rc2:
        risk["profile_assigned"]    = _field("Profile assigned",    risk.get("profile_assigned"),    "ff_risk_profile")
        risk["capacity_for_loss"]   = _field("Capacity for loss",   risk.get("capacity_for_loss"),   "ff_risk_cfl")
    with rc3:
        risk["investment_time_horizon"] = _field("Investment time horizon", risk.get("investment_time_horizon"), "ff_risk_horizon")
    risk["client_own_words"] = _field("Client's own words on risk", risk.get("client_own_words"), "ff_risk_words", height=80)
    data["risk"] = risk

    st.markdown("")

    _section("Estate Planning", "📋")
    ep = data.get("estate_planning", {})
    ec1, ec2 = st.columns(2)
    with ec1:
        ep["will_in_place"]       = _field("Will in place?",       ep.get("will_in_place"),       "ff_ep_will")
        ep["will_date"]           = _field("Will date",            ep.get("will_date"),            "ff_ep_willdate")
        ep["lpa_in_place"]        = _field("LPA in place?",        ep.get("lpa_in_place"),         "ff_ep_lpa")
    with ec2:
        ep["iht_position"]        = _field("IHT position",         ep.get("iht_position"),         "ff_ep_iht")
        ep["beneficiaries_noted"] = _field("Beneficiaries noted?", ep.get("beneficiaries_noted"),  "ff_ep_bens")
        ep["trust_arrangements"]  = _field("Trust arrangements",   ep.get("trust_arrangements"),   "ff_ep_trust")
    data["estate_planning"] = ep

    st.markdown("")

    _section("Tax Position", "💼")
    tax = data.get("tax", {})
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        tax["client1_tax_band"]     = _field("Client 1 tax band",       tax.get("client1_tax_band"),     "ff_tax_c1band")
        tax["client2_tax_band"]     = _field("Client 2 tax band",       tax.get("client2_tax_band"),     "ff_tax_c2band")
    with tc2:
        tax["cgt_position"]         = _field("CGT position",            tax.get("cgt_position"),         "ff_tax_cgt")
        tax["annual_allowance_used"]= _field("Annual allowance used",   tax.get("annual_allowance_used"),"ff_tax_aa")
    with tc3:
        tax["isa_allowance_used"]   = _field("ISA allowance used",      tax.get("isa_allowance_used"),   "ff_tax_isa")
        tax["notes"]                = _field("Tax notes",               tax.get("notes"),                "ff_tax_notes")
    data["tax"] = tax

    st.session_state._ff_data = data

    st.markdown("---")

    st.markdown("#### Step 3 — Confirm and generate")
    st.caption("Once you're happy with the data above, click Confirm and Generate. The report will be produced from the verified information.")

    remaining_flags = [f for f in data.get("flags", []) if f and f.strip()]
    if remaining_flags:
        st.warning(f"{len(remaining_flags)} item(s) still flagged above — review them before generating if possible.")

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([2, 1, 1, 1])
    with btn_col2:
        if st.button("Save details", use_container_width=True):
            update_client_fact_find(cid, data, fact_find_to_notes(data))
            st.success("Saved to client profile.")
    with btn_col3:
        if st.button("Start over", use_container_width=True):
            st.session_state.pop("_ff_data", None)
            st.session_state.pop("_ff_notes", None)
            st.rerun()
    with btn_col4:
        confirm = st.button("Confirm & Generate Report", type="primary", use_container_width=True)

    if confirm:
        structured_notes = fact_find_to_notes(data)
        update_client_fact_find(cid, data, structured_notes)
        st.session_state._ff_confirmed_data  = data
        st.session_state._ff_structured_notes = structured_notes
        st.session_state._show_ff_outputs = True

    if st.session_state.get("_show_ff_outputs"):
        data2  = st.session_state.get("_ff_confirmed_data", data)
        notes2 = st.session_state.get("_ff_structured_notes", "")
        cname  = st.session_state.active_client_name or "Client"

        st.markdown("---")
        st.markdown("#### Confirmed — choose what to do next")

        out1, out2, out3 = st.columns(3)

        with out1:
            st.markdown("""
            <div class="pfx-card" style="min-height:90px;">
                <div style="font-weight:700;color:#1F3346;margin-bottom:4px;">Generate Suitability Report</div>
                <div style="font-size:0.82rem;color:#7A8A88;">Use verified fact-find data to generate the full report.</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Generate Report →", use_container_width=True, key="ff_to_report"):
                st.session_state.pop("_ff_data", None)
                st.session_state.pop("_ff_notes", None)
                st.session_state.pop("_show_ff_outputs", None)
                st.session_state.page = "generate"
                st.session_state._prefill_notes = notes2
                st.rerun()

        with out2:
            st.markdown("""
            <div class="pfx-card" style="min-height:90px;border-left:4px solid #12B8A6;">
                <div style="font-weight:700;color:#1F3346;margin-bottom:4px;">Download Fact-Find (Client Copy)</div>
                <div style="font-size:0.82rem;color:#7A8A88;">Clean form with blank lines — for client review and signature.</div>
            </div>""", unsafe_allow_html=True)
            from documents.factfind_doc import build_factfind_doc
            fn = cname.replace(" ", "_").replace("&", "and")
            adviser = st.session_state.user.get("email","") if st.session_state.user else ""
            client_buf = build_factfind_doc(cname, adviser, "", data2, client_facing=True)
            st.download_button(
                "Download Client Copy (.docx)", data=client_buf,
                file_name=f"Parafinix_{fn}_FactFind_Client.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True, key="ff_dl_client"
            )

        with out3:
            st.markdown("""
            <div class="pfx-card" style="min-height:90px;border-left:4px solid #C0392B;">
                <div style="font-weight:700;color:#1F3346;margin-bottom:4px;">Download Fact-Find (Internal Copy)</div>
                <div style="font-size:0.82rem;color:#7A8A88;">Gap analysis with [MISSING] flags — paraplanner working document.</div>
            </div>""", unsafe_allow_html=True)
            internal_buf = build_factfind_doc(cname, adviser, "", data2, client_facing=False)
            st.download_button(
                "Download Internal Copy (.docx)", data=internal_buf,
                file_name=f"Parafinix_{fn}_FactFind_Internal.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True, key="ff_dl_internal"
            )