"""
routers/documents.py — Document generation endpoints.

Returns documents in two formats:
  - JSON with base64_content (for programmatic use)
  - Direct file download via ?download=true query param (for browser)

POST /documents/suitability
POST /documents/compliance
POST /documents/factfind
"""
import base64
from datetime import date
from fastapi import APIRouter, Query
from services.pdf_export import docx_to_pdf
from fastapi.responses import StreamingResponse
from middleware.auth import get_current_user, AuthenticatedUser
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


def _safe_name(name: str) -> str:
    return name.replace(" ", "_").replace("&", "and").replace("/", "-")


def _filename(client_name: str, doc_type: str) -> str:
    return f"Parafinix_{_safe_name(client_name)}_{doc_type}_{date.today().strftime('%d%b%Y')}.docx"


PDF_MIME = "application/pdf"


def _respond(buf, filename: str, download: bool, fmt: str = "docx"):
    """Returns DOCX or PDF as streaming download or base64 JSON."""
    if fmt == "pdf":
        buf = docx_to_pdf(buf)
        filename = filename.replace(".docx", ".pdf")
        mime = PDF_MIME
    else:
        mime = DOCX_MIME

    if download:
        return StreamingResponse(
            buf,
            media_type=mime,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return {
        "filename": filename,
        "base64_content": base64.b64encode(buf.getvalue()).decode("utf-8"),
        "mime_type": mime,
        "content_disposition": f'attachment; filename="{filename}"',
    }


@router.post("/suitability")
async def build_suitability(
    body: BuildSuitabilityDocRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    download: bool = Query(default=False, description="Set true for direct browser download"),
):
    """Builds the suitability report .docx."""
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
    return _respond(buf, _filename(body.client_name, "Suitability_Report"), download, format)


@router.post("/compliance")
async def build_compliance(
    body: BuildComplianceDocRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    download: bool = Query(default=False),
):
    """Builds the compliance review .docx."""
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
    return _respond(buf, _filename(body.client_name, "Compliance_Review"), download, format)


@router.post("/factfind")
async def build_factfind(
    body: BuildFactFindDocRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    download: bool = Query(default=False),
):
    """Builds the fact-find .docx (client copy or internal)."""
    buf = build_factfind_doc(
        client_name=body.client_name,
        adviser_name=body.adviser_name or "",
        firm_name=body.firm_name or "",
        data=body.fact_find_data,
        client_facing=body.client_facing,
    )
    doc_type = "FactFind_Client" if body.client_facing else "FactFind_Internal"
    return _respond(buf, _filename(body.client_name, doc_type), download, format)
