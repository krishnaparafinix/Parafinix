"""
routers/generate.py — AI generation endpoints.

Generation pipeline matches the proven Streamlit implementation exactly:
  - 2-pass generation (same as Streamlit _run_generation)
  - Same prompts, same token limits, same context windows
  - Same compliance check logic
  - No simplifications or approximations
"""
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, AuthenticatedUser
from services.preflight import run_preflight
from services.fact_find import extract_fact_find, fact_find_to_notes
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import (
    SYSTEM_PROMPT, FULL_REPORT_PROMPT,
    PASS2_PROMPT, TEMPLATE_PROMPT,
    COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS,
)

router = APIRouter()


class PreflightRequest(BaseModel):
    notes: str


class ExtractFactFindRequest(BaseModel):
    notes: str


class GenerateReportRequest(BaseModel):
    client_name: str
    adviser_name: Optional[str] = ""
    firm_name: Optional[str] = ""
    basis: Optional[str] = "Independent"
    charges: Optional[str] = ""
    report_ref: Optional[str] = ""
    notes: str
    template_text: Optional[str] = ""


@router.post("/preflight")
async def preflight(
    body: PreflightRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Fast pre-flight quality scan on meeting notes."""
    result = run_preflight(body.notes)
    return result


@router.post("/extract")
async def extract(
    body: ExtractFactFindRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Extracts structured fact-find data from raw notes.
    Identical to the Streamlit extract_fact_find() call.
    """
    from fastapi import HTTPException
    data = extract_fact_find(body.notes)
    if data is None:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed — AI returned unexpected format. Please try again."
        )
    flags = [f for f in data.get("flags", []) if f and f.strip()]
    return {"data": data, "flags": flags}


@router.post("/report")
async def generate_report(
    body: GenerateReportRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    2-pass suitability report generation — exact copy of Streamlit _run_generation().

    Pass 1: Executive Summary + Sections 1-5 (circumstances, objectives, risk, analysis)
    Pass 2: Section 6 (recommendations) + Sections 7-11 + Paraplanner Check
    Compliance: 28-point COBS 9A review of the combined output

    This is the proven implementation that produced the working Anurag report.
    Do not change this without testing against the Streamlit reference output.
    """
    notes   = body.notes
    cname   = body.client_name
    adviser = body.adviser_name or ""
    firm    = body.firm_name or ""
    basis   = body.basis or "Independent"
    charges = body.charges or ""
    ref     = body.report_ref or ""
    template = body.template_text or ""

    # ── PASS 1: Sections 1–5 ─────────────────────────────────
    # Exact match to Streamlit: same prompt construction, same token limit
    if template:
        p1_msg = (
            f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n"
            f"Basis: {basis}\nCharges: {charges}\n\nNOTES:\n{notes}\n\n"
            f"{TEMPLATE_PROMPT.format(template_text=template[:3000])}\n\n"
            f"Write the first half following the template. Use markdown tables."
        )
    else:
        p1_msg = (
            f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n"
            f"Basis: {basis}\nCharges: {charges}\n\nNOTES:\n{notes}\n\n"
            f"{FULL_REPORT_PROMPT}"
        )

    part1 = call_drafting_model(SYSTEM_PROMPT, p1_msg, max_tokens=6000)

    # ── PASS 2: Recommendations + Sections 7–11 ──────────────
    # Exact match to Streamlit: part1[:3000] context, same prompt
    p2_msg = (
        f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n\n"
        f"NOTES:\n{notes}\n\nSECTIONS 1-5:\n{part1[:3000]}\n\n{PASS2_PROMPT}"
    )
    part2 = call_drafting_model(SYSTEM_PROMPT, p2_msg, max_tokens=6000)

    # ── COMPLIANCE CHECK ─────────────────────────────────────
    # Exact match to Streamlit: combined[:7000], same system + items
    combined = part1 + "\n\n" + part2
    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined[:7000]}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=2500,
    )

    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)

    if fails > 2:
        rag = "RED"
    elif flags > 5 or fails > 0:
        rag = "AMBER"
    else:
        rag = "GREEN"

    # Return same structure as Streamlit _run_generation()
    # part3 and part4 empty — matches Streamlit which also returns them as ""
    return {
        "part1": part1,
        "part2": part2,
        "part3": "",
        "part4": "",
        "check_text": check_text,
        "passes": passes,
        "flags": flags,
        "fails": fails,
        "rag_rating": rag,
        "adviser_name": adviser,
        "firm_name": firm,
        "basis": basis,
        "charges": charges,
        "report_ref": ref,
    }
