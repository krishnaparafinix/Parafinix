"""
routers/generate.py — AI generation endpoints.

POST   /generate/preflight   → fast pre-flight quality scan (~5 seconds)
POST   /generate/extract     → fact-find extraction from raw text
POST   /generate/report      → full 4-pass suitability report generation
"""
from fastapi import APIRouter
from middleware.auth import CurrentUser
from models.requests import PreflightRequest, ExtractFactFindRequest, GenerateReportRequest

router = APIRouter()


@router.post("/preflight")
async def preflight(body: PreflightRequest, user: CurrentUser):
    """
    Fast pre-flight quality scan on meeting notes before full generation.
    Returns confidence rating, what was found, and what is missing.
    """
    # Phase 4: result = run_preflight(body.notes); return result
    return {"message": "stub", "notes_length": len(body.notes)}


@router.post("/extract")
async def extract_fact_find(body: ExtractFactFindRequest, user: CurrentUser):
    """
    Extracts ~60 structured fields from raw meeting notes or PDF text.
    Returns a structured fact-find JSON the Lovable frontend renders as an editable form.
    """
    # Phase 6: result = extract_fact_find_service(body.notes); return result
    return {"message": "stub", "notes_length": len(body.notes)}


@router.post("/report")
async def generate_report(body: GenerateReportRequest, user: CurrentUser):
    """
    Runs the full 4-pass suitability report generation pipeline.
    Pass 1: Executive Summary + Sections 1-5
    Pass 2: Recommendations (first half)
    Pass 3: Recommendations (second half)
    Pass 4: Sections 7-11 + Paraplanner Check
    Returns all four parts plus compliance check results.
    """
    # Phase 4: result = run_four_pass_generation(body); return result
    return {
        "message": "stub",
        "client_name": body.client_name,
        "notes_length": len(body.notes),
    }
