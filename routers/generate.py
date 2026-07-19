"""
Suitability report uses 3-pass generation to ensure complete output:
  Pass 1: Sections 1-5 (8000 tokens)
  Pass 2: All of Section 6 - recommendations (8000 tokens)
  Pass 3: Sections 7-11 + Paraplanner Check (6000 tokens)
  Compliance: 28-point COBS 9A review (independent endpoint, full report text)

This matches the quality and structure of the reference Anurag report,
with increased tokens to prevent the mid-section cutoff.
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, AuthenticatedUser
from services.preflight import run_preflight
from services.fact_find import extract_fact_find, fact_find_to_notes
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import (
    SYSTEM_PROMPT, FULL_REPORT_PROMPT,
    PASS2_PROMPT, PASS3_PROMPT, PASS4_PROMPT,
    TEMPLATE_PROMPT,
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


class GenerateComplianceRequest(BaseModel):
    part1: str
    part2: str
    part3: Optional[str] = ""
    part4: Optional[str] = ""


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
    """Extracts structured fact-find data from raw notes."""
    data = extract_fact_find(body.notes)
    if data is None:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed — AI returned unexpected format. Please try again."
        )
    flags = [f for f in data.get("flags", []) if f and f.strip()]
    return {"data": data, "flags": flags}


def _run_compliance_check(combined: str) -> dict:
    """
    Runs the 28-point COBS 9A compliance review against the FULL report text.
    No truncation — a truncated input causes the model to falsely FAIL items
    (assets, pensions, recommendations) that actually exist later in the report.
    """
    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=4000,
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

    return {
        "check_text": check_text,
        "passes": passes,
        "flags": flags,
        "fails": fails,
        "rag_rating": rag,
    }


@router.post("/compliance")
async def generate_compliance(
    body: GenerateComplianceRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Runs the compliance review independently of /generate/report — pass in
    an already-generated report's parts (from /generate/report's response,
    or from a saved case) to re-run or refresh the compliance check without
    regenerating the whole suitability report.
    """
    combined = f"{body.part1}\n\n{body.part2}\n\n{body.part3}\n\n{body.part4}"
    return _run_compliance_check(combined)


@router.post("/report")
async def generate_report(
    body: GenerateReportRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    3-pass suitability report generation.

    Produces the same quality as the reference Anurag/David reports.
    Increased token limits prevent the mid-recommendation cutoff.

    Pass 1 (8000 tokens): Executive Summary + Sections 1-5
      - Client circumstances, objectives, risk analysis
      - Net worth table, pension analysis, retirement scenarios

    Pass 2 (8000 tokens): Section 6 — All recommendations
      - Every recommendation with full 8-part structure
      - Current position, why change needed, recommendation,
        suitability rationale, benefits, risks, alternatives, outcome

    Pass 3 (6000 tokens): Sections 7-11 + Paraplanner Check
      - Product information, charges, tax, risks, next steps
      - Paraplanner verification checklist

    Compliance runs automatically against the full combined text.
    """
    notes   = body.notes
    cname   = body.client_name
    adviser = body.adviser_name or ""
    firm    = body.firm_name or ""
    basis   = body.basis or "Independent"
    charges = body.charges or ""
    ref     = body.report_ref or ""
    template = body.template_text or ""

    # ── PASS 1: Executive Summary + Sections 1–5 ─────────────
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
            f"{FULL_REPORT_PROMPT}\n\n"
            f"IMPORTANT: Do NOT include a [PARAPLANNER CHECK] section in this pass. "
            f"That will be added later, after all sections are complete. "
            f"Stop cleanly and completely after Section 5 with no further content."
        )
    part1 = call_drafting_model(SYSTEM_PROMPT, p1_msg, max_tokens=8000)

    # ── PASS 2: All of Section 6 — Recommendations ───────────
    p2_msg = (
        f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n\n"
        f"NOTES:\n{notes}\n\n"
        f"SECTIONS 1-5 ALREADY DRAFTED:\n{part1[:3000]}\n\n"
        f"{PASS2_PROMPT}\n\n"
        f"IMPORTANT: Write ALL recommendations for this client — do not stop early. "
        f"Cover every relevant area from the notes. Each recommendation must use the "
        f"full 8-part structure. Do not add a 'recommendations continue' note."
    )
    part2 = call_drafting_model(SYSTEM_PROMPT, p2_msg, max_tokens=8000)

    # ── PASS 3: Sections 7–11 + Paraplanner Check ────────────
    p3_msg = (
        f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n\n"
        f"NOTES:\n{notes}\n\n"
        f"RECOMMENDATIONS ALREADY WRITTEN (do not repeat):\n{part2[:2000]}\n\n"
        f"{PASS4_PROMPT}"
    )
    part3 = call_drafting_model(SYSTEM_PROMPT, p3_msg, max_tokens=6000)

    # ── COMPLIANCE CHECK ──────────────────────────────────────
    combined = f"{part1}\n\n{part2}\n\n{part3}"
    compliance_result = _run_compliance_check(combined)

    return {
        "part1": part1,
        "part2": part2,
        "part3": part3,
        "part4": "",
        "check_text": compliance_result["check_text"],
        "passes": compliance_result["passes"],
        "flags": compliance_result["flags"],
        "fails": compliance_result["fails"],
        "rag_rating": compliance_result["rag_rating"],
        "adviser_name": adviser,
        "firm_name": firm,
        "basis": basis,
        "charges": charges,
        "report_ref": ref,
    }