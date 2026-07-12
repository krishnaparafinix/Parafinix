"""
routers/documents.py — Document generation endpoints.

POST   /documents/suitability   → build suitability .docx → base64
POST   /documents/compliance    → build compliance .docx  → base64
POST   /documents/factfind      → build fact-find .docx   → base64

All endpoints return base64-encoded Word documents.
Lovable decodes client-side and triggers a browser download.
No files are stored on the server — regenerate on demand.
"""
from fastapi import APIRouter
from middleware.auth import CurrentUser
from models.requests import (
    BuildSuitabilityDocRequest,
    BuildComplianceDocRequest,
    BuildFactFindDocRequest,
)

router = APIRouter()


@router.post("/suitability")
async def build_suitability(body: BuildSuitabilityDocRequest, user: CurrentUser):
    """Builds and returns a base64-encoded suitability report .docx."""
    # Phase 5: buf = build_suitability_doc(...); return base64_response(buf, filename)
    return {"message": "stub", "client_name": body.client_name}


@router.post("/compliance")
async def build_compliance(body: BuildComplianceDocRequest, user: CurrentUser):
    """Builds and returns a base64-encoded compliance review .docx."""
    # Phase 5: buf = build_compliance_doc(...); return base64_response(buf, filename)
    return {"message": "stub", "client_name": body.client_name}


@router.post("/factfind")
async def build_factfind(body: BuildFactFindDocRequest, user: CurrentUser):
    """
    Builds and returns a base64-encoded fact-find .docx.
    client_facing=True  → blank lines for missing fields (for client review)
    client_facing=False → [MISSING] in red (internal paraplanner copy)
    """
    # Phase 5: buf = build_factfind_doc(...); return base64_response(buf, filename)
    return {"message": "stub", "client_name": body.client_name}
