"""
routers/documents.py — Document generation endpoints.

POST   /documents/suitability  → build suitability .docx → base64
POST   /documents/compliance   → build compliance .docx  → base64
POST   /documents/factfind     → build fact-find .docx   → base64

All documents returned as base64-encoded strings.
Lovable decodes client-side and triggers a browser download.
No files stored on the server — regenerate on demand.
"""
import base64
from datetime import date
from fastapi import APIRouter
from middleware.auth import CurrentUser
from models.requests import (
    BuildSuitabilityDocRequest,
    BuildComplianceDocRequest,
    BuildFactFindDocRequest,
)
from services.document_builder.suitability_doc import build_suitability_doc
from services.document_builder.compliance_doc import build_compliance_doc
from services.document_builder.factfind_doc import build_factfind_doc

router = APIRouter()

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _to_base64(buf) -> str:
    """Converts an io.BytesIO buffer to a base64 string."""
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _filename(client_name: str, doc_type: str) -> str:
    safe = client_name.replace(" ", "_").replace("&", "and")
    today = date.today().strftime("%d%b%Y")
    return f"Parafinix_{safe}_{doc_type}_{today}.docx"


@router.post("/suitability")
async def build_suitability(body: BuildSuitabilityDocRequest, user: CurrentUser):
    """
    Builds a complete suitability report .docx from the four generated parts.
    Returns the file as a base64-encoded string.
    """
    buf = build_suitability_doc(
        client_name=body.client_name,
        adviser_name=body.adviser_name or "",
        firm_name=body.firm_name or "",
        basis=body.basis or "",
        charges=body.charges or "",
        report_ref=body.report_ref or "",
        part1=body.report_part1,
        part2=body.report_part2 or "",
        part3=body.report_part3 or "",
        part4=body.report_part4 or "",
    )
    return {
        "filename": _filename(body.client_name, "Suitability_Report"),
        "base64_content": _to_base64(buf),
        "mime_type": DOCX_MIME,
    }


@router.post("/compliance")
async def build_compliance(body: BuildComplianceDocRequest, user: CurrentUser):
    """
    Builds a compliance review .docx with RAG rating, 28-point check, sign-off page.
    Returns the file as a base64-encoded string.
    """
    buf = build_compliance_doc(
        client_name=body.client_name,
        adviser_name=body.adviser_name or "",
        firm_name=body.firm_name or "",
        report_ref=body.report_ref or "",
        check_text=body.check_text,
        passes=body.passes,
        flags=body.flags,
        missing=body.fails,
    )
    return {
        "filename": _filename(body.client_name, "Compliance_Review"),
        "base64_content": _to_base64(buf),
        "mime_type": DOCX_MIME,
    }


@router.post("/factfind")
async def build_factfind(body: BuildFactFindDocRequest, user: CurrentUser):
    """
    Builds a fact-find .docx document.
    client_facing=True  → blank lines for missing fields (for client review/signature)
    client_facing=False → [MISSING] in red + gap analysis (internal paraplanner copy)
    Returns the file as a base64-encoded string.
    """
    buf = build_factfind_doc(
        client_name=body.client_name,
        adviser_name=body.adviser_name or "",
        firm_name=body.firm_name or "",
        data=body.fact_find_data,
        client_facing=body.client_facing,
    )
    doc_type = "FactFind_Client" if body.client_facing else "FactFind_Internal"
    return {
        "filename": _filename(body.client_name, doc_type),
        "base64_content": _to_base64(buf),
        "mime_type": DOCX_MIME,
    }
