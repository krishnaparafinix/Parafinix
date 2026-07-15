"""
routers/ai_chat.py — AI assistant and compliance endpoints.

POST /ai/chat              → paraplanning Q&A — returns {"reply": "..."}
POST /ai/compliance/rerun  → rerun 28-point check on a saved case
POST /ai/compliance/fix    → fix suggestion for a compliance flag
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, require_admin, AuthenticatedUser
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS
import services.database as db

router = APIRouter()

CHAT_SYSTEM = """You are a Senior Chartered Financial Planner and UK compliance expert with 25 years of experience. You assist paraplanners and financial advisers with FCA regulations, COBS 9A suitability requirements, pension rules, ISA and investment strategies, IHT planning, and Consumer Duty obligations. Give clear, practical, professional answers in British English."""


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""


class ComplianceRerunRequest(BaseModel):
    case_id: str


class ComplianceFixRequest(BaseModel):
    flag_item: str
    report_section: str
    client_context: Optional[str] = ""


def _token(r: Request) -> str:
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


@router.post("/chat")
async def ai_chat(
    body: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """General AI assistant. Returns {"reply": "..."}"""
    msg = body.message
    if body.context:
        msg = f"Context:\n{body.context[:2000]}\n\nQuestion: {body.message}"
    reply = call_compliance_model(CHAT_SYSTEM, msg, max_tokens=1500)
    return {"reply": reply}


@router.post("/compliance/rerun")
async def compliance_rerun(
    request: Request,
    body: ComplianceRerunRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Reruns the 28-point compliance check on a saved case."""
    token = _token(request)
    case = db.get_case(body.case_id, token)
    combined = "\n\n".join(filter(None, [
        case.get("report_part1", ""),
        case.get("report_part2", ""),
        case.get("report_part3", ""),
        case.get("report_part4", ""),
    ]))
    if not combined.strip():
        raise HTTPException(400, "No report content found in this case.")

    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined[:7000]}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=2500,
    )
    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)
    rag    = "RED" if fails > 2 else ("AMBER" if flags > 5 or fails > 0 else "GREEN")

    try:
        from supabase import create_client
        from config import settings
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        client.auth.set_session(token, token)
        client.table("cases").update({
            "compliance_result": check_text,
            "passes": passes, "flags": flags, "fails": fails, "rag_rating": rag,
        }).eq("id", body.case_id).execute()
    except Exception as e:
        raise HTTPException(500, f"Database update failed: {e}")

    return {
        "check_text": check_text,
        "passes": passes, "flags": flags, "fails": fails,
        "rag_rating": rag, "message": "Compliance check updated.",
    }


@router.post("/compliance/fix")
async def compliance_fix(
    body: ComplianceFixRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns a specific fix suggestion for a compliance flag."""
    prompt = (
        f"Compliance flag: {body.flag_item}\n\n"
        f"Report section:\n{body.report_section[:2000]}\n\n"
        f"Client context: {body.client_context[:500]}\n\n"
        "Write a specific fix. Include: what text to add, which section, "
        "and a ready-to-use draft paragraph. Use professional British English."
    )
    suggestion = call_drafting_model(
        "You are a Senior UK Compliance Manager. Provide specific, actionable fixes for suitability report compliance gaps.",
        prompt, max_tokens=1000,
    )
    return {"flag": body.flag_item, "suggestion": suggestion}
