"""
routers/generate.py — AI generation endpoints.

POST   /generate/preflight   → fast pre-flight quality scan
POST   /generate/extract     → fact-find extraction from raw text
POST   /generate/report      → full 4-pass suitability report generation
"""
from fastapi import APIRouter, Request, Depends
from middleware.auth import get_current_user, AuthenticatedUser
from models.requests import PreflightRequest, ExtractFactFindRequest, GenerateReportRequest
from services.preflight import run_preflight
from services.fact_find import extract_fact_find, fact_find_to_notes
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import (
    SYSTEM_PROMPT, FULL_REPORT_PROMPT,
    PASS2_PROMPT, PASS3_PROMPT, PASS4_PROMPT,
    TEMPLATE_PROMPT, COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS,
)

router = APIRouter()


@router.post("/preflight")
async def preflight(body: PreflightRequest, user: AuthenticatedUser = Depends(get_current_user)):
    """
    Fast pre-flight quality scan on meeting notes.
    Returns confidence rating, what was found, and what is missing.
    Uses the compliance model (faster/cheaper than Opus).
    """
    result = run_preflight(body.notes)
    return result


@router.post("/extract")
async def extract(body: ExtractFactFindRequest, user: AuthenticatedUser = Depends(get_current_user)):
    """
    Extracts ~60 structured fields from raw meeting notes or PDF text.
    Returns a structured fact-find JSON the Lovable frontend renders
    as an editable form. User reviews and confirms before generating.
    """
    data = extract_fact_find(body.notes)
    if data is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="Extraction failed — AI returned unexpected format. Please try again."
        )
    flags = [f for f in data.get("flags", []) if f and f.strip()]
    return {"data": data, "flags": flags}


@router.post("/report")
async def generate_report(body: GenerateReportRequest, user: AuthenticatedUser = Depends(get_current_user)):
    """
    Runs the full 4-pass suitability report generation pipeline.

    Pass 1: Executive Summary + Sections 1-5 (circumstances, objectives, risk)
    Pass 2: Recommendations first half
    Pass 3: Recommendations second half
    Pass 4: Sections 7-11 (charges, tax, risks, next steps) + Paraplanner Check

    Returns all four parts plus the 28-point compliance check results.
    Total AI capacity: 24,000 tokens.
    """
    notes = body.notes
    cname = body.client_name
    adviser = body.adviser_name or ""
    firm = body.firm_name or ""
    basis = body.basis or "Independent"
    charges = body.charges or ""
    ref = body.report_ref or ""
    template = body.template_text or ""

    # ── PASS 1 ───────────────────────────────────────────────
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

    # ── PASS 2 ───────────────────────────────────────────────
    p2_msg = (
        f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n\n"
        f"NOTES:\n{notes}\n\n"
        f"SECTIONS 1-5 ALREADY DRAFTED:\n{part1[:2500]}\n\n"
        f"{PASS2_PROMPT}"
    )
    part2 = call_drafting_model(SYSTEM_PROMPT, p2_msg, max_tokens=6000)

    # ── PASS 3 ───────────────────────────────────────────────
    p3_msg = (
        f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n\n"
        f"NOTES:\n{notes}\n\n"
        f"RECOMMENDATIONS SO FAR (do not repeat):\n{part2[:2500]}\n\n"
        f"{PASS3_PROMPT}"
    )
    part3 = call_drafting_model(SYSTEM_PROMPT, p3_msg, max_tokens=6000)

    # ── PASS 4 ───────────────────────────────────────────────
    p4_msg = (
        f"Client: {cname}\nAdviser: {adviser}\nFirm: {firm}\n\n"
        f"NOTES:\n{notes}\n\n"
        f"RECOMMENDATIONS DRAFTED:\n{part2[:1200]}...{part3[:1200]}\n\n"
        f"{PASS4_PROMPT}"
    )
    part4 = call_drafting_model(SYSTEM_PROMPT, p4_msg, max_tokens=6000)

    # ── COMPLIANCE CHECK ─────────────────────────────────────
    combined = f"{part1}\n\n{part2}\n\n{part3}\n\n{part4}"
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

    return {
        "part1": part1,
        "part2": part2,
        "part3": part3,
        "part4": part4,
        "check_text": check_text,
        "passes": passes,
        "flags": flags,
        "fails": fails,
        "rag_rating": rag,
    }
